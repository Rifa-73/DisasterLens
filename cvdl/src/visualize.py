import os
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = PROJECT_ROOT / "outputs"

IMAGE_PATH = Path(
    "/Users/rifa/Downloads/FloodNet-Supervised_v1/val/val-org-img/10169.jpg"
)

MASK_PATH = Path(
    "/Users/rifa/Downloads/FloodNet-Supervised_v1/val/val-label-img/10169_lab.png"
)

PREDICTION_PATH = OUTPUT_DIR / "10169_prediction_mask.png"


# ============================================================
# CLASS NAMES
# ============================================================

CLASS_NAMES = {
    0: "Background",
    1: "Building-Flooded",
    2: "Building-Non-Flooded",
    3: "Road-Flooded",
    4: "Road-Non-Flooded",
    5: "Water",
    6: "Tree",
    7: "Vehicle",
    8: "Pool",
    9: "Grass"
}


# ============================================================
# CHECK FILES
# ============================================================

print("=" * 70)
print("CVDL VISUALIZATION")
print("=" * 70)

print("\nChecking files...")

if not IMAGE_PATH.exists():
    raise FileNotFoundError(
        f"Original image not found:\n{IMAGE_PATH}"
    )

if not MASK_PATH.exists():
    raise FileNotFoundError(
        f"Ground truth mask not found:\n{MASK_PATH}"
    )

if not PREDICTION_PATH.exists():
    raise FileNotFoundError(
        f"Prediction mask not found:\n{PREDICTION_PATH}\n"
        "Run predict.py first."
    )

print("✓ Original image found")
print("✓ Ground truth mask found")
print("✓ Prediction mask found")


# ============================================================
# LOAD IMAGES
# ============================================================

original = Image.open(IMAGE_PATH).convert("RGB")
ground_truth = np.array(Image.open(MASK_PATH))
prediction = np.array(Image.open(PREDICTION_PATH))


# ============================================================
# HANDLE MASK FORMAT
# ============================================================

# If masks have an unnecessary channel dimension
if ground_truth.ndim == 3:
    ground_truth = ground_truth[:, :, 0]

if prediction.ndim == 3:
    prediction = prediction[:, :, 0]


# ============================================================
# RESIZE PREDICTION IF NECESSARY
# ============================================================

if prediction.shape != ground_truth.shape:

    prediction = np.array(
        Image.fromarray(prediction.astype(np.uint8)).resize(
            (ground_truth.shape[1], ground_truth.shape[0]),
            Image.Resampling.NEAREST
        )
    )


# ============================================================
# CALCULATE PIXEL ACCURACY
# ============================================================

pixel_accuracy = np.mean(
    prediction == ground_truth
)


# ============================================================
# CALCULATE PER-CLASS IoU
# ============================================================

ious = {}

for class_id, class_name in CLASS_NAMES.items():

    gt = ground_truth == class_id
    pred = prediction == class_id

    intersection = np.logical_and(gt, pred).sum()
    union = np.logical_or(gt, pred).sum()

    if union == 0:
        iou = np.nan
    else:
        iou = intersection / union

    ious[class_id] = iou


# Foreground classes only
foreground_ious = [
    iou for class_id, iou in ious.items()
    if class_id != 0 and not np.isnan(iou)
]

if foreground_ious:
    foreground_miou = np.mean(foreground_ious)
else:
    foreground_miou = 0.0


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

print(f"\nPixel Accuracy : {pixel_accuracy:.4f}")
print(f"Foreground mIoU: {foreground_miou:.4f}")

print("\nPer-Class IoU:")

for class_id, class_name in CLASS_NAMES.items():

    if np.isnan(ious[class_id]):
        print(f"{class_id:2d} {class_name:<22}: N/A")
    else:
        print(
            f"{class_id:2d} {class_name:<22}: "
            f"{ious[class_id]:.4f}"
        )


# ============================================================
# CREATE VISUALIZATION
# ============================================================

plt.figure(figsize=(18, 6))


# ------------------------------------------------------------
# ORIGINAL
# ------------------------------------------------------------

plt.subplot(1, 3, 1)

plt.imshow(original)

plt.title(
    "Original Image",
    fontsize=16,
    fontweight="bold"
)

plt.axis("off")


# ------------------------------------------------------------
# GROUND TRUTH
# ------------------------------------------------------------

plt.subplot(1, 3, 2)

plt.imshow(ground_truth, cmap="tab10", vmin=0, vmax=9)

plt.title(
    "Ground Truth",
    fontsize=16,
    fontweight="bold"
)

plt.axis("off")


# ------------------------------------------------------------
# PREDICTION
# ------------------------------------------------------------

plt.subplot(1, 3, 3)

plt.imshow(prediction, cmap="tab10", vmin=0, vmax=9)

plt.title(
    "CVDL Prediction",
    fontsize=16,
    fontweight="bold"
)

plt.axis("off")


# ============================================================
# SAVE VISUALIZATION
# ============================================================

output_path = OUTPUT_DIR / "cvdl_comparison_10169.png"

plt.tight_layout()

plt.savefig(
    output_path,
    dpi=200,
    bbox_inches="tight"
)

plt.show()


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("VISUALIZATION COMPLETE")
print("=" * 70)

print(f"\nSaved to:")
print(output_path)

print("\n✓ Original")
print("✓ Ground Truth")
print("✓ CVDL Prediction")
print(f"✓ Pixel Accuracy: {pixel_accuracy:.4f}")
print(f"✓ Foreground mIoU: {foreground_miou:.4f}")