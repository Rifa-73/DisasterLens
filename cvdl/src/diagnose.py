import sys
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
# SETTINGS
# ============================================================

NUM_CLASSES = 10

IMAGE_SIZE = (512, 512)

MODEL_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "best_model_weighted.pth"
)

# Validation folders
IMAGE_DIR = Path(
    "/Users/rifa/Downloads/FloodNet-Supervised_v1/val/val-org-img"
)

MASK_DIR = Path(
    "/Users/rifa/Downloads/FloodNet-Supervised_v1/val/val-label-img"
)


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
# DEVICE
# ============================================================

if torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

print("=" * 70)
print("DEVICE:", device)
print("=" * 70)


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading model...")

model = FloodNetUNet(
    num_classes=NUM_CLASSES
)

checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
    weights_only=False
)

if "model_state_dict" in checkpoint:
    model.load_state_dict(
        checkpoint["model_state_dict"]
    )
else:
    model.load_state_dict(checkpoint)

model = model.to(device)
model.eval()

print("Model loaded successfully!")
print("Model:", MODEL_PATH)


# ============================================================
# IMAGE TRANSFORM
# MUST MATCH TRAINING
# ============================================================

image_transform = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor()
])

mask_transform = transforms.Resize(
    IMAGE_SIZE,
    interpolation=transforms.InterpolationMode.NEAREST
)


# ============================================================
# FIND VALIDATION IMAGES
# ============================================================

image_files = sorted(
    list(IMAGE_DIR.glob("*.jpg")) +
    list(IMAGE_DIR.glob("*.png")) +
    list(IMAGE_DIR.glob("*.jpeg"))
)

if len(image_files) == 0:
    raise FileNotFoundError(
        f"No images found in: {IMAGE_DIR}"
    )

print("\nValidation images found:", len(image_files))


# ============================================================
# CONFUSION MATRIX
# ============================================================

confusion_matrix = np.zeros(
    (NUM_CLASSES, NUM_CLASSES),
    dtype=np.int64
)


# ============================================================
# PIXEL COUNTS
# ============================================================

gt_pixel_counts = np.zeros(
    NUM_CLASSES,
    dtype=np.int64
)

pred_pixel_counts = np.zeros(
    NUM_CLASSES,
    dtype=np.int64
)


# ============================================================
# PROCESS ALL VALIDATION IMAGES
# ============================================================

print("\nRunning validation analysis...\n")

for index, image_path in enumerate(image_files):

    image_name = image_path.stem

    mask_path = MASK_DIR / f"{image_name}_lab.png"

    if not mask_path.exists():

        print(
            f"WARNING: Mask not found for {image_name}"
        )

        continue


    # --------------------------------------------------------
    # LOAD IMAGE
    # --------------------------------------------------------

    image = Image.open(
        image_path
    ).convert("RGB")

    image_tensor = image_transform(
        image
    ).unsqueeze(0)

    image_tensor = image_tensor.to(
        device
    )


    # --------------------------------------------------------
    # LOAD GROUND TRUTH MASK
    # --------------------------------------------------------

    mask = Image.open(
        mask_path
    ).convert("L")

    mask = mask_transform(mask)

    gt = np.array(
        mask,
        dtype=np.int64
    )


    # --------------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------------

    with torch.no_grad():

        output = model(
            image_tensor
        )

        prediction = torch.argmax(
            output,
            dim=1
        )

        prediction = prediction.squeeze(0)

        prediction = (
            prediction
            .cpu()
            .numpy()
            .astype(np.int64)
        )


    # --------------------------------------------------------
    # PIXEL DISTRIBUTION
    # --------------------------------------------------------

    for class_id in range(NUM_CLASSES):

        gt_pixel_counts[class_id] += np.sum(
            gt == class_id
        )

        pred_pixel_counts[class_id] += np.sum(
            prediction == class_id
        )


    # --------------------------------------------------------
    # CONFUSION MATRIX
    #
    # ROW    = Ground Truth
    # COLUMN = Prediction
    # --------------------------------------------------------

    valid = (
        (gt >= 0)
        & (gt < NUM_CLASSES)
    )

    gt_flat = gt[valid].flatten()
    pred_flat = prediction[valid].flatten()

    for true_class, predicted_class in zip(
        gt_flat,
        pred_flat
    ):

        confusion_matrix[
            true_class,
            predicted_class
        ] += 1


    if (index + 1) % 50 == 0:

        print(
            f"Processed {index + 1}/"
            f"{len(image_files)} images"
        )


# ============================================================
# PIXEL DISTRIBUTION
# ============================================================

total_gt_pixels = gt_pixel_counts.sum()
total_pred_pixels = pred_pixel_counts.sum()

print("\n")
print("=" * 70)
print("PIXEL DISTRIBUTION")
print("=" * 70)

print(
    f"{'Class':<25}"
    f"{'GT Pixels':>15}"
    f"{'GT %':>10}"
    f"{'Pred Pixels':>15}"
    f"{'Pred %':>10}"
)

print("-" * 70)

for class_id in range(NUM_CLASSES):

    gt_count = gt_pixel_counts[class_id]
    pred_count = pred_pixel_counts[class_id]

    gt_percent = (
        gt_count / total_gt_pixels * 100
    )

    pred_percent = (
        pred_count / total_pred_pixels * 100
    )

    print(
        f"{class_id} "
        f"{CLASS_NAMES[class_id]:<21}"
        f"{gt_count:>15,}"
        f"{gt_percent:>9.2f}%"
        f"{pred_count:>15,}"
        f"{pred_percent:>9.2f}%"
    )


# ============================================================
# DETECT OVER-PREDICTION
# ============================================================

print("\n")
print("=" * 70)
print("OVER / UNDER PREDICTION")
print("=" * 70)

for class_id in range(NUM_CLASSES):

    gt_percent = (
        gt_pixel_counts[class_id]
        / total_gt_pixels
        * 100
    )

    pred_percent = (
        pred_pixel_counts[class_id]
        / total_pred_pixels
        * 100
    )

    difference = pred_percent - gt_percent

    if difference > 5:

        status = "OVER-PREDICTED"

    elif difference < -5:

        status = "UNDER-PREDICTED"

    else:

        status = "OK"

    print(
        f"{class_id:2d} "
        f"{CLASS_NAMES[class_id]:<25} "
        f"GT={gt_percent:6.2f}%  "
        f"Pred={pred_percent:6.2f}%  "
        f"Diff={difference:+6.2f}%  "
        f"{status}"
    )


# ============================================================
# PER CLASS IoU
# ============================================================

print("\n")
print("=" * 70)
print("PER-CLASS IoU")
print("=" * 70)

ious = []

for class_id in range(NUM_CLASSES):

    true_positive = confusion_matrix[
        class_id,
        class_id
    ]

    false_positive = (
        confusion_matrix[:, class_id].sum()
        - true_positive
    )

    false_negative = (
        confusion_matrix[class_id, :].sum()
        - true_positive
    )

    denominator = (
        true_positive
        + false_positive
        + false_negative
    )

    if denominator == 0:

        iou = float("nan")

    else:

        iou = (
            true_positive
            / denominator
        )

    ious.append(iou)

    print(
        f"Class {class_id} "
        f"({CLASS_NAMES[class_id]:<23}) : "
        f"{iou:.4f}"
    )


# ============================================================
# mIoU INCLUDING BACKGROUND
# ============================================================

valid_ious = [
    iou
    for iou in ious
    if not np.isnan(iou)
]

miou_all = np.mean(
    valid_ious
)

print("\nMean IoU INCLUDING background:")
print(f"{miou_all:.4f}")


# ============================================================
# mIoU EXCLUDING BACKGROUND
# ============================================================

foreground_ious = [
    ious[class_id]
    for class_id in range(1, NUM_CLASSES)
    if not np.isnan(ious[class_id])
]

miou_foreground = np.mean(
    foreground_ious
)

print("\nMean IoU EXCLUDING background:")
print(f"{miou_foreground:.4f}")


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\n")
print("=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print(
    "Rows = Ground Truth"
)

print(
    "Columns = Prediction\n"
)

header = "GT\\Pred"

for class_id in range(NUM_CLASSES):

    header += (
        f"{class_id:>8}"
    )

print(header)

print("-" * 90)

for true_class in range(NUM_CLASSES):

    row = (
        f"{true_class:>7}"
    )

    for predicted_class in range(NUM_CLASSES):

        row += (
            f"{confusion_matrix[true_class, predicted_class]:>8}"
        )

    print(row)


# ============================================================
# GRASS SPECIFIC ANALYSIS
# ============================================================

GRASS = 9

grass_gt = gt_pixel_counts[GRASS]
grass_pred = pred_pixel_counts[GRASS]

grass_gt_percent = (
    grass_gt / total_gt_pixels * 100
)

grass_pred_percent = (
    grass_pred / total_pred_pixels * 100
)

print("\n")
print("=" * 70)
print("GRASS ANALYSIS")
print("=" * 70)

print(
    f"Ground Truth Grass : "
    f"{grass_gt_percent:.2f}%"
)

print(
    f"Predicted Grass    : "
    f"{grass_pred_percent:.2f}%"
)

print(
    f"Difference         : "
    f"{grass_pred_percent - grass_gt_percent:+.2f}%"
)


if grass_pred_percent > grass_gt_percent + 5:

    print(
        "\n⚠️ Grass is significantly OVER-PREDICTED."
    )

elif grass_pred_percent < grass_gt_percent - 5:

    print(
        "\n⚠️ Grass is UNDER-PREDICTED."
    )

else:

    print(
        "\n✅ Grass prediction amount is reasonably close."
    )


# ============================================================
# SAVE CONFUSION MATRIX
# ============================================================

output_dir = (
    PROJECT_ROOT
    / "outputs"
)

output_dir.mkdir(
    exist_ok=True
)

np.savetxt(
    output_dir / "confusion_matrix.csv",
    confusion_matrix,
    delimiter=",",
    fmt="%d"
)

print("\nConfusion matrix saved to:")

print(
    output_dir
    / "confusion_matrix.csv"
)


print("\n")
print("=" * 70)
print("DIAGNOSTIC ANALYSIS COMPLETE")
print("=" * 70)