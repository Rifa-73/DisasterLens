import sys
from pathlib import Path

import cv2
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

MODEL_PATH = (
    REPO_ROOT
    / "cvdl"
    / "outputs"
    / "best_model_weighted.pth"
)

IMAGE_FOLDER = (
    Path.home()
    / "Downloads"
    / "FloodNet-Supervised_v1"
    / "test"
    / "test-org-img"
)

OUTPUT_FOLDER = (
    REPO_ROOT
    / "cvdl"
    / "outputs"
    / "batch_visualizations"
)

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
# COLORS
# ============================================================

CLASS_COLORS = {
    0: (0, 0, 0),          # Background
    1: (255, 0, 0),        # Building-Flooded
    2: (0, 255, 0),        # Building-Non-Flooded
    3: (255, 100, 0),      # Road-Flooded
    4: (100, 255, 0),      # Road-Non-Flooded
    5: (0, 0, 255),        # Water
    6: (0, 255, 255),      # Tree
    7: (255, 0, 255),      # Vehicle
    8: (255, 255, 0),      # Pool
    9: (150, 150, 150)     # Grass
}


# ============================================================
# FLOOD CLASSES
# ============================================================

FLOOD_CLASSES = {
    1,
    3,
    5
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
# LOAD MODEL
# ============================================================

def load_model():

    print("\nLoading U-Net model...")

    model = FloodNetUNet(
        num_classes=NUM_CLASSES
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
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

    model.to(DEVICE)

    model.eval()

    print(
        f"Model loaded on: {DEVICE}"
    )

    return model


# ============================================================
# LOAD IMAGE
# ============================================================

def load_image(image_path):

    image = Image.open(
        image_path
    ).convert("RGB")

    original = np.array(
        image
    )

    resized = image.resize(
        IMAGE_SIZE
    )

    image_array = np.array(
        resized
    ).astype(
        np.float32
    ) / 255.0

    tensor = torch.from_numpy(
        image_array
    ).permute(
        2,
        0,
        1
    ).unsqueeze(0)

    tensor = tensor.to(
        DEVICE
    )

    return original, tensor


# ============================================================
# PREDICT MASK
# ============================================================

def predict_mask(
    model,
    tensor
):

    with torch.no_grad():

        outputs = model(
            tensor
        )

        adjusted_outputs = (
            outputs.clone()
        )

        # Same flood-aware bias used
        # in your current predict_api.py

        adjusted_outputs[
            :,
            1,
            :,
            :
        ] += 0.10

        adjusted_outputs[
            :,
            3,
            :,
            :
        ] += 0.18

        adjusted_outputs[
            :,
            5,
            :,
            :
        ] += 0.05

        mask = torch.argmax(
            adjusted_outputs,
            dim=1
        )

    return mask.squeeze(
        0
    ).cpu().numpy()


# ============================================================
# CREATE COLOR MASK
# ============================================================

def create_color_mask(
    mask
):

    h, w = mask.shape

    color_mask = np.zeros(
        (
            h,
            w,
            3
        ),
        dtype=np.uint8
    )

    for class_id, color in CLASS_COLORS.items():

        color_mask[
            mask == class_id
        ] = color

    return color_mask


# ============================================================
# CALCULATE CLASS PERCENTAGES
# ============================================================

def calculate_class_percentages(
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

        percentages[
            class_name
        ] = round(
            float(percentage),
            2
        )

    return percentages


# ============================================================
# CREATE OVERLAY
# ============================================================

def create_overlay(
    original,
    mask
):

    original_resized = cv2.resize(
        original,
        (
            IMAGE_SIZE[0],
            IMAGE_SIZE[1]
        )
    )

    color_mask = create_color_mask(
        mask
    )

    # --------------------------------------------------------
    # Only show predicted classes
    # --------------------------------------------------------

    overlay = cv2.addWeighted(
        original_resized,
        0.60,
        color_mask,
        0.40,
        0
    )

    return original_resized, color_mask, overlay


# ============================================================
# ADD INFORMATION PANEL
# ============================================================

def add_information(
    overlay,
    percentages
):

    image = overlay.copy()

    flood_coverage = sum(
        percentages.get(
            class_name,
            0.0
        )
        for class_name in [
            "Building-Flooded",
            "Road-Flooded",
            "Water"
        ]
    )

    flood_coverage = min(
        flood_coverage,
        100.0
    )

    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    if flood_coverage >= 30:

        severity = "HIGH"

    elif flood_coverage >= 10:

        severity = "MEDIUM"

    elif flood_coverage > 0:

        severity = "LOW"

    else:

        severity = "NONE"

    # --------------------------------------------------------
    # Panel
    # --------------------------------------------------------

    panel_height = 110

    panel = np.zeros(
        (
            panel_height,
            image.shape[1],
            3
        ),
        dtype=np.uint8
    )

    image = np.vstack(
        [
            panel,
            image
        ]
    )

    # --------------------------------------------------------
    # Text
    # --------------------------------------------------------

    cv2.putText(
        image,
        f"Flood Coverage: {flood_coverage:.2f}%",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        image,
        f"Severity: {severity}",
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    return image, flood_coverage, severity


# ============================================================
# PROCESS ONE IMAGE
# ============================================================

def process_image(
    model,
    image_path,
    output_path
):

    print(
        f"\nProcessing: "
        f"{image_path.name}"
    )

    original, tensor = load_image(
        image_path
    )

    mask = predict_mask(
        model,
        tensor
    )

    percentages = (
        calculate_class_percentages(
            mask
        )
    )

    original_resized, color_mask, overlay = (
        create_overlay(
            original,
            mask
        )
    )

    final_image, flood_coverage, severity = (
        add_information(
            overlay,
            percentages
        )
    )

    cv2.imwrite(
        str(output_path),
        cv2.cvtColor(
            final_image,
            cv2.COLOR_RGB2BGR
        )
    )

    print(
        f"    Flood Coverage: "
        f"{flood_coverage:.2f}%"
    )

    print(
        f"    Severity: "
        f"{severity}"
    )

    print(
        f"    Saved: "
        f"{output_path.name}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("      DISASTERLENS - BATCH SEGMENTATION VISUALIZATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = load_model()

    # --------------------------------------------------------
    # Find images
    # --------------------------------------------------------

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"
    }

    image_files = sorted(
        [
            file
            for file
            in IMAGE_FOLDER.iterdir()
            if file.is_file()
            and file.suffix.lower()
            in image_extensions
        ]
    )

    if not image_files:

        print(
            "\nNo images found."
        )

        return

    # --------------------------------------------------------
    # IMPORTANT:
    # For first test, only process top 5 images
    # --------------------------------------------------------

    selected_images = image_files[:5]

    print(
        f"\nProcessing first "
        f"{len(selected_images)} images."
    )

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    for index, image_path in enumerate(
        selected_images,
        start=1
    ):

        output_name = (
            f"{index}_"
            f"{image_path.stem}_"
            f"overlay.png"
        )

        output_path = (
            OUTPUT_FOLDER
            / output_name
        )

        try:

            process_image(
                model,
                image_path,
                output_path
            )

        except Exception as e:

            print(
                f"    ERROR: {e}"
            )

    # --------------------------------------------------------
    # Done
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("VISUALIZATION COMPLETE")
    print("=" * 70)

    print(
        f"\nOutput folder:\n"
        f"{OUTPUT_FOLDER}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()