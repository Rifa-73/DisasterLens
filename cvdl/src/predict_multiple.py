import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image


# ============================================================
# PATH SETUP
# ============================================================

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

CVDL_ROOT = REPO_ROOT / "cvdl"
CVDL_SRC = CVDL_ROOT / "src"
CVDL_MODELS = CVDL_ROOT / "models"

for path in [CVDL_SRC, CVDL_MODELS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


# ============================================================
# IMPORT MODEL
# ============================================================

from cvdl_model import FloodNetUNet


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = CVDL_ROOT / "outputs" / "best_model_weighted.pth"

IMAGE_SIZE = (512, 512)

NUM_CLASSES = 10


# ============================================================
# CLASS NAMES
# ============================================================

CLASS_NAMES = [
    "Background",
    "Building-Flooded",
    "Building-Non-Flooded",
    "Road-Flooded",
    "Road-Non-Flooded",
    "Water",
    "Tree",
    "Vehicle",
    "Pool",
    "Grass"
]


# ============================================================
# FLOOD CLASSES
# ============================================================

FLOOD_CLASSES = {
    1,  # Building-Flooded
    3,  # Road-Flooded
    5   # Water
}


# ============================================================
# FLOOD LOGIT BIAS
# Same logic as predict_api.py
# ============================================================

FLOOD_LOGIT_BIAS = {
    1: 0.10,
    3: 0.18,
    5: 0.05
}


# ============================================================
# DEVICE
# ============================================================

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")


# ============================================================
# PREDICTOR CLASS
# ============================================================

class FloodMultiplePredictor:

    def __init__(self, model_path=None):

        self.model_path = (
            Path(model_path)
            if model_path
            else MODEL_PATH
        )

        self.device = DEVICE

        self.model = self._load_model()


    # ========================================================
    # LOAD MODEL
    # ========================================================

    def _load_model(self):

        print("\nLoading U-Net model...")

        model = FloodNetUNet(
            num_classes=NUM_CLASSES
        )

        checkpoint = torch.load(
            self.model_path,
            map_location=self.device,
            weights_only=False
        )

        if "model_state_dict" in checkpoint:

            model.load_state_dict(
                checkpoint["model_state_dict"]
            )

        else:

            model.load_state_dict(
                checkpoint
            )

        model.to(self.device)
        model.eval()

        print(
            f"Model loaded on: {self.device}"
        )

        return model


    # ========================================================
    # LOAD IMAGE
    # ========================================================

    def _load_image(self, image):

        if isinstance(image, (str, Path)):

            image = Image.open(image)

        elif isinstance(image, bytes):

            import io

            image = Image.open(
                io.BytesIO(image)
            )

        elif not isinstance(image, Image.Image):

            raise TypeError(
                "Image must be a file path, bytes, "
                "or PIL Image."
            )

        image = image.convert("RGB")

        original_size = image.size

        resized = image.resize(
            IMAGE_SIZE
        )

        image_array = (
            np.array(resized)
            .astype(np.float32)
            / 255.0
        )

        tensor = torch.from_numpy(
            image_array
        ).permute(
            2, 0, 1
        ).unsqueeze(0)

        tensor = tensor.to(
            self.device
        )

        return tensor, original_size


    # ========================================================
    # PREDICT SINGLE IMAGE
    # ========================================================

    def predict_single(self, image):

        tensor, original_size = self._load_image(
            image
        )

        with torch.no_grad():

            outputs = self.model(
                tensor
            )

            adjusted_outputs = (
                outputs.clone()
            )

            for class_id, bias in FLOOD_LOGIT_BIAS.items():

                adjusted_outputs[
                    :, class_id, :, :
                ] += bias

            mask = torch.argmax(
                adjusted_outputs,
                dim=1
            )

        mask = (
            mask.squeeze(0)
            .cpu()
            .numpy()
        )

        return mask


    # ========================================================
    # FLOOD COVERAGE
    # ========================================================

    def _calculate_flood_coverage(
        self,
        mask
    ):

        total_pixels = mask.size

        flood_pixels = np.isin(
            mask,
            list(FLOOD_CLASSES)
        ).sum()

        flood_percentage = (
            flood_pixels
            / total_pixels
            * 100
        )

        return round(
            min(
                float(flood_percentage),
                100.0
            ),
            2
        )


    # ========================================================
    # CLASS PERCENTAGES
    # ========================================================

    def _calculate_class_percentages(
        self,
        mask
    ):

        total_pixels = mask.size

        percentages = {}

        for class_id, class_name in enumerate(
            CLASS_NAMES
        ):

            count = np.sum(
                mask == class_id
            )

            percentage = (
                count
                / total_pixels
                * 100
            )

            percentages[class_name] = round(
                float(percentage),
                2
            )

        return percentages


    # ========================================================
    # SEVERITY
    # ========================================================

    def _get_severity(
        self,
        flood_coverage
    ):

        if flood_coverage >= 30:

            return "High"

        elif flood_coverage >= 10:

            return "Medium"

        elif flood_coverage > 0:

            return "Low"

        else:

            return "None"


    # ========================================================
    # PREDICT MULTIPLE IMAGES
    # ========================================================

    def predict_multiple(
        self,
        images
    ):

        if not images:

            raise ValueError(
                "No images provided."
            )

        results = []

        for index, image in enumerate(
            images,
            start=1
        ):

            # Get image name
            if isinstance(
                image,
                (str, Path)
            ):

                image_name = Path(
                    image
                ).name

            else:

                image_name = (
                    f"image_{index}"
                )

            # Prediction
            mask = self.predict_single(
                image
            )

            # Flood coverage
            flood_coverage = (
                self._calculate_flood_coverage(
                    mask
                )
            )

            # Class percentages
            class_percentages = (
                self._calculate_class_percentages(
                    mask
                )
            )

            # Severity
            severity = self._get_severity(
                flood_coverage
            )

            result = {

                "rank": None,

                "image": image_name,

                "flood_coverage_pct":
                    flood_coverage,

                "severity":
                    severity,

                "class_percentages":
                    class_percentages
            }

            results.append(
                result
            )


        # ====================================================
        # SORT BY FLOOD COVERAGE
        # ====================================================

        results.sort(
            key=lambda x:
                x["flood_coverage_pct"],
            reverse=True
        )


        # ====================================================
        # ASSIGN RANK
        # ====================================================

        for rank, result in enumerate(
            results,
            start=1
        ):

            result["rank"] = rank


        # ====================================================
        # HIGHEST SEVERITY IMAGE
        # ====================================================

        highest = results[0]


        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        response = {

            "total_images":
                len(results),

            "results":
                results,

            "highest_severity":
                {

                    "image":
                        highest["image"],

                    "flood_coverage_pct":
                        highest[
                            "flood_coverage_pct"
                        ],

                    "severity":
                        highest["severity"],

                    "rank":
                        highest["rank"]
                }
        }

        return response


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print(
        "DISASTERLENS - MULTIPLE IMAGE PREDICTION"
    )
    print("=" * 70)


    # Test images
    test_folder = (
        Path.home()
        / "Downloads"
        / "FloodNet-Supervised_v1"
        / "test"
        / "test-org-img"
    )


    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"
    }


    image_files = sorted([

        file

        for file in test_folder.iterdir()

        if (
            file.is_file()
            and file.suffix.lower()
            in image_extensions
        )

    ])


    if not image_files:

        print(
            "\nNo test images found."
        )

        sys.exit(1)


    # Use first 5 images
    selected_images = image_files[:5]


    print(
        f"\nTesting with "
        f"{len(selected_images)} images..."
    )


    predictor = FloodMultiplePredictor()


    response = predictor.predict_multiple(
        selected_images
    )


    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)


    for result in response["results"]:

        print(
            f"\nRank {result['rank']}"
        )

        print(
            f"Image: "
            f"{result['image']}"
        )

        print(
            f"Flood Coverage: "
            f"{result['flood_coverage_pct']:.2f}%"
        )

        print(
            f"Severity: "
            f"{result['severity']}"
        )


    print("\n" + "-" * 70)

    print(
        "HIGHEST SEVERITY IMAGE"
    )

    print(
        f"Image: "
        f"{response['highest_severity']['image']}"
    )

    print(
        f"Flood Coverage: "
        f"{response['highest_severity']['flood_coverage_pct']:.2f}%"
    )

    print(
        f"Severity: "
        f"{response['highest_severity']['severity']}"
    )

    print(
        f"Rank: "
        f"{response['highest_severity']['rank']}"
    )


    print("\n" + "=" * 70)
    print("MULTIPLE IMAGE PREDICTION COMPLETE")
    print("=" * 70)