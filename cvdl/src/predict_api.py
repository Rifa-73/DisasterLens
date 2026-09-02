"""
predict.py
============================================================
Inference module for the FloodNet U-Net segmentation model.

This is meant to be imported directly by the backend (FastAPI)
so it can turn an uploaded image into:
  1. A segmentation mask (numpy array, one class id per pixel)
  2. Per-class area percentages
  3. A single "severity score" summarizing flood damage

Usage as a library:
------------------------------------------------------------
    from predict import FloodPredictor

    predictor = FloodPredictor("outputs/best_model_ce_dice.pth")

    # From a file path
    result = predictor.predict("some_image.jpg")

    # From raw bytes (e.g. an uploaded file in FastAPI)
    with open("some_image.jpg", "rb") as f:
        image_bytes = f.read()
    result = predictor.predict(image_bytes)

    print(result["severity_score"])
    print(result["class_percentages"])

Usage from the command line (for quick testing):
------------------------------------------------------------
    python predict.py path/to/image.jpg
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

# ------------------------------------------------------------
# PROJECT ROOT (matches train.py's setup)
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.cvdl_model import FloodNetUNet


# ============================================================
# CONFIG — must match training config
# ============================================================

NUM_CLASSES = 10
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

# Classes that indicate actual flood damage (used for severity scoring).
# Weight = how much that class contributes to the severity score.
# Tune these based on how "bad" each class is for disaster response.
SEVERITY_WEIGHTS = {
    "Building-Flooded": 3.0,
    "Road-Flooded": 2.0,
    "Water": 1.0,       # standing water outside expected areas
    "Vehicle": 0.5,      # stranded vehicles, minor signal
    "Pool": 0.3,         # usually not disaster-relevant, low weight
}


# ============================================================
# PREDICTOR
# ============================================================

class FloodPredictor:

    def __init__(self, model_path, device=None):

        self.model_path = Path(model_path)

        if device is not None:
            self.device = device
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.model = FloodNetUNet(num_classes=NUM_CLASSES)

        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)

        # Support both raw state_dict and full checkpoint dict formats
        if "model_state_dict" in checkpoint:
            self.model.load_state_dict(checkpoint["model_state_dict"])
        else:
            self.model.load_state_dict(checkpoint)

        self.model.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize(IMAGE_SIZE),
            transforms.ToTensor()
        ])

    # --------------------------------------------------------
    # Load an image from a file path, bytes, or a PIL Image
    # --------------------------------------------------------
    def _load_image(self, image_input):

        if isinstance(image_input, Image.Image):
            image = image_input.convert("RGB")

        elif isinstance(image_input, (bytes, bytearray)):
            image = Image.open(io.BytesIO(image_input)).convert("RGB")

        elif isinstance(image_input, (str, Path)):
            image = Image.open(image_input).convert("RGB")

        else:
            raise TypeError(
                "image_input must be a file path, bytes, or PIL.Image"
            )

        return image

    # --------------------------------------------------------
    # Run the model and return a raw class-id mask (H, W)
    # --------------------------------------------------------
    def predict_mask(self, image_input):

        image = self._load_image(image_input)
        original_size = image.size  # (W, H)

        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)
            mask = torch.argmax(outputs, dim=1).squeeze(0)

        mask = mask.cpu().numpy().astype(np.uint8)

        return mask, original_size

    # --------------------------------------------------------
    # Full prediction: mask + per-class stats + severity score
    # --------------------------------------------------------
    def predict(self, image_input, resize_mask_to_original=False):

        mask, original_size = self.predict_mask(image_input)

        total_pixels = mask.size

        class_pixel_counts = {}
        class_percentages = {}

        for class_id, class_name in enumerate(CLASS_NAMES):
            count = int((mask == class_id).sum())
            class_pixel_counts[class_name] = count
            class_percentages[class_name] = round(
                100.0 * count / total_pixels, 2
            )

        severity_score = self._compute_severity(class_percentages)

        result = {
            "mask": mask,  # numpy array (H, W), class id per pixel
            "mask_shape": mask.shape,
            "original_size": original_size,  # (W, H) of input image
            "class_pixel_counts": class_pixel_counts,
            "class_percentages": class_percentages,
            "severity_score": severity_score,
            "severity_label": self._severity_label(severity_score),
        }

        if resize_mask_to_original:
            mask_img = Image.fromarray(mask).resize(
                original_size, resample=Image.NEAREST
            )
            result["mask_original_size"] = np.array(mask_img)

        return result

    # --------------------------------------------------------
    # Severity scoring: weighted sum of flood-relevant class %s,
    # normalized to a 0-100 scale.
    # --------------------------------------------------------
    def _compute_severity(self, class_percentages):

        raw_score = 0.0

        for class_name, weight in SEVERITY_WEIGHTS.items():
            raw_score += weight * class_percentages.get(class_name, 0.0)

        # Normalize against the max possible raw score (all severity
        # weight classes at 100%) so the result is roughly 0-100.
        max_possible = sum(SEVERITY_WEIGHTS.values()) * 100.0
        normalized = (raw_score / max_possible) * 100.0

        return round(min(normalized, 100.0), 2)

    def _severity_label(self, score):

        if score >= 50:
            return "High"
        elif score >= 20:
            return "Medium"
        elif score > 0:
            return "Low"
        else:
            return "None"

    # --------------------------------------------------------
    # Save a color-coded visualization of the mask to disk
    # --------------------------------------------------------
    def save_visualization(self, mask, output_path):

        # Simple fixed color palette, one color per class
        palette = np.array([
            [0, 0, 0],        # Background
            [255, 0, 0],      # Building-Flooded
            [180, 0, 0],      # Building-Non-Flooded
            [0, 0, 255],      # Road-Flooded
            [0, 0, 150],      # Road-Non-Flooded
            [0, 255, 255],    # Water
            [0, 128, 0],      # Tree
            [255, 255, 0],    # Vehicle
            [0, 255, 0],      # Pool
            [144, 238, 144],  # Grass
        ], dtype=np.uint8)

        color_mask = palette[mask]
        Image.fromarray(color_mask).save(output_path)


# ============================================================
# COMMAND-LINE USAGE (quick manual testing)
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python predict.py <image_path> [model_path]")
        sys.exit(1)

    image_path = sys.argv[1]

    model_path = (
        sys.argv[2]
        if len(sys.argv) > 2
        else str(PROJECT_ROOT / "outputs" / "best_model_ce_dice.pth")
    )

    predictor = FloodPredictor(model_path)

    result = predictor.predict(image_path)

    # Don't dump the raw mask array to stdout, just the summary
    printable = {
        k: v
        for k, v in result.items()
        if k not in ("mask", "mask_original_size")
    }

    print(json.dumps(printable, indent=2))

    predictor.save_visualization(
        result["mask"],
        "prediction_visualization.png"
    )

    print("\nSaved visualization to prediction_visualization.png")