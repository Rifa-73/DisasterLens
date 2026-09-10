"""
============================================================
predict.py
============================================================

Inference module for the FloodNet U-Net segmentation model.

This is meant to be imported directly by the backend (FastAPI)
so it can turn an uploaded image into:

1. A segmentation mask
2. Per-class area percentages
3. A single severity score
============================================================
"""

import sys
import io
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import transforms


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from models.cvdl_model import FloodNetUNet


# ============================================================
# CONFIG
# ============================================================

NUM_CLASSES = 10

# Match the latest training resolution
IMAGE_SIZE = (512, 512)


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
    "Grass",
]


# ============================================================
# SEVERITY WEIGHTS
# ============================================================

SEVERITY_WEIGHTS = {
    "Building-Flooded": 3.0,
    "Road-Flooded": 2.0,
    "Water": 1.0,
    "Vehicle": 0.5,
    "Pool": 0.3,
}


# ============================================================
# FLOOD-AWARE PREDICTION
# ============================================================

# Small inference-time preference for flood-related classes.
#
# This does NOT retrain or modify the model.
# It only adjusts the logits slightly before argmax.
#
# Road-Flooded gets the strongest adjustment because it was
# the weakest flooded class during validation.

FLOOD_LOGIT_BIAS = {
    1: 0.10,   # Building-Flooded
    3: 0.18,   # Road-Flooded
    5: 0.05,   # Water
}


# ============================================================
# PREDICTOR
# ============================================================

class FloodPredictor:

    def __init__(self, model_path, device=None):

        self.model_path = Path(model_path)


        # ----------------------------------------------------
        # Select device
        # ----------------------------------------------------

        if device is not None:

            self.device = device

        elif torch.backends.mps.is_available():

            self.device = torch.device("mps")

        elif torch.cuda.is_available():

            self.device = torch.device("cuda")

        else:

            self.device = torch.device("cpu")


        # ----------------------------------------------------
        # Create model
        # ----------------------------------------------------

        self.model = FloodNetUNet(
            num_classes=NUM_CLASSES
        )


        # ----------------------------------------------------
        # Load checkpoint
        # ----------------------------------------------------

        checkpoint = torch.load(
            self.model_path,
            map_location=self.device,
            weights_only=False
        )


        # ----------------------------------------------------
        # Support full checkpoint
        # ----------------------------------------------------

        if "model_state_dict" in checkpoint:

            self.model.load_state_dict(
                checkpoint["model_state_dict"]
            )

        else:

            self.model.load_state_dict(
                checkpoint
            )


        # ----------------------------------------------------
        # Move model to device
        # ----------------------------------------------------

        self.model.to(
            self.device
        )

        self.model.eval()


        # ----------------------------------------------------
        # Image transformation
        # ----------------------------------------------------

        self.transform = transforms.Compose([

            transforms.Resize(
                IMAGE_SIZE
            ),

            transforms.ToTensor()

        ])


    # ========================================================
    # LOAD IMAGE
    # ========================================================

    def _load_image(self, image_input):

        if isinstance(
            image_input,
            Image.Image
        ):

            image = image_input.convert(
                "RGB"
            )


        elif isinstance(
            image_input,
            (bytes, bytearray)
        ):

            image = Image.open(
                io.BytesIO(image_input)
            ).convert(
                "RGB"
            )


        elif isinstance(
            image_input,
            (str, Path)
        ):

            image = Image.open(
                image_input
            ).convert(
                "RGB"
            )


        else:

            raise TypeError(
                "image_input must be a file path, "
                "bytes, or PIL.Image"
            )


        return image


    # ========================================================
    # FLOOD-AWARE PREDICTION
    # ========================================================

    def predict_mask(self, image_input):

        image = self._load_image(
            image_input
        )


        original_size = image.size


        # ----------------------------------------------------
        # Convert image to tensor
        # ----------------------------------------------------

        tensor = self.transform(
            image
        ).unsqueeze(
            0
        ).to(
            self.device
        )


        # ----------------------------------------------------
        # Model inference
        # ----------------------------------------------------

        with torch.no_grad():

            outputs = self.model(
                tensor
            )


            # ------------------------------------------------
            # Make a copy so original model output is not
            # modified.
            # ------------------------------------------------

            adjusted_outputs = outputs.clone()


            # ------------------------------------------------
            # Apply small flood-aware bias
            # ------------------------------------------------

            for class_id, bias in FLOOD_LOGIT_BIAS.items():

                adjusted_outputs[
                    :,
                    class_id,
                    :,
                    :
                ] += bias


            # ------------------------------------------------
            # Final class prediction
            # ------------------------------------------------

            mask = torch.argmax(
                adjusted_outputs,
                dim=1
            ).squeeze(0)


        # ----------------------------------------------------
        # Convert to numpy
        # ----------------------------------------------------

        mask = mask.cpu().numpy().astype(
            np.uint8
        )


        return mask, original_size


    # ========================================================
    # FULL PREDICTION
    # ========================================================

    def predict(
        self,
        image_input,
        resize_mask_to_original=False
    ):

        mask, original_size = self.predict_mask(
            image_input
        )


        total_pixels = mask.size


        class_pixel_counts = {}

        class_percentages = {}


        # ----------------------------------------------------
        # Calculate class statistics
        # ----------------------------------------------------

        for class_id, class_name in enumerate(
            CLASS_NAMES
        ):

            count = int(
                (mask == class_id).sum()
            )


            class_pixel_counts[
                class_name
            ] = count


            class_percentages[
                class_name
            ] = round(
                100.0 * count / total_pixels,
                2
            )


        # ----------------------------------------------------
        # Calculate severity
        # ----------------------------------------------------

        severity_score = self._compute_severity(
            class_percentages
        )


        # ----------------------------------------------------
        # Create result
        # ----------------------------------------------------

        result = {

            "mask":
                mask,

            "mask_shape":
                mask.shape,

            "original_size":
                original_size,

            "class_pixel_counts":
                class_pixel_counts,

            "class_percentages":
                class_percentages,

            "severity_score":
                severity_score,

            "severity_label":
                self._severity_label(
                    severity_score
                ),

        }


        # ----------------------------------------------------
        # Optional original-size mask
        # ----------------------------------------------------

        if resize_mask_to_original:

            mask_img = Image.fromarray(
                mask
            ).resize(
                original_size,
                resample=Image.NEAREST
            )


            result[
                "mask_original_size"
            ] = np.array(
                mask_img
            )


        return result


    # ========================================================
    # SEVERITY SCORE
    # ========================================================

    def _compute_severity(
        self,
        class_percentages
    ):

        # ----------------------------------------------------
        # Actual flood coverage
        #
        # Building-Flooded + Road-Flooded + Water
        # ----------------------------------------------------

        flood_coverage = (

            class_percentages.get(
                "Building-Flooded",
                0.0
            )

            +

            class_percentages.get(
                "Road-Flooded",
                0.0
            )

            +

            class_percentages.get(
                "Water",
                0.0
            )

        )


        # ----------------------------------------------------
        # Keep score between 0 and 100
        # ----------------------------------------------------

        flood_coverage = min(
            flood_coverage,
            100.0
        )


        return round(
            flood_coverage,
            2
        )


    # ========================================================
    # SEVERITY LABEL
    # ========================================================

    def _severity_label(
        self,
        score
    ):

        # 30% or more flood coverage
        # = High severity

        if score >= 30:

            return "High"


        # 10% - 29.99%
        # = Medium severity

        elif score >= 10:

            return "Medium"


        # More than 0%
        # = Low severity

        elif score > 0:

            return "Low"


        else:

            return "None"


    # ========================================================
    # SAVE VISUALIZATION
    # ========================================================

    def save_visualization(
        self,
        mask,
        output_path
    ):

        # ----------------------------------------------------
        # Fixed color palette
        # ----------------------------------------------------

        palette = np.array([

            [0, 0, 0],          # Background

            [255, 0, 0],        # Building-Flooded

            [180, 0, 0],        # Building-Non-Flooded

            [0, 0, 255],        # Road-Flooded

            [0, 0, 150],        # Road-Non-Flooded

            [0, 255, 255],      # Water

            [0, 128, 0],        # Tree

            [255, 255, 0],      # Vehicle

            [0, 255, 0],        # Pool

            [144, 238, 144],    # Grass

        ], dtype=np.uint8)


        color_mask = palette[
            mask
        ]


        Image.fromarray(
            color_mask
        ).save(
            output_path
        )


# ============================================================
# COMMAND LINE USAGE
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "Usage: python predict.py "
            "<image_path> [model_path]"
        )

        sys.exit(1)


    image_path = sys.argv[1]


    model_path = (

        sys.argv[2]

        if len(sys.argv) > 2

        else str(
            PROJECT_ROOT
            /
            "outputs"
            /
            "best_model_weighted.pth"
        )

    )


    predictor = FloodPredictor(
        model_path
    )


    result = predictor.predict(
        image_path
    )


    # --------------------------------------------------------
    # Don't print raw mask
    # --------------------------------------------------------

    printable = {

        k: v

        for k, v in result.items()

        if k not in (
            "mask",
            "mask_original_size"
        )

    }


    print(
        json.dumps(
            printable,
            indent=2
        )
    )


    # --------------------------------------------------------
    # Save visualization
    # --------------------------------------------------------

    predictor.save_visualization(
        result["mask"],
        "prediction_visualization.png"
    )


    print(
        "\nSaved visualization to "
        "prediction_visualization.png"
    )