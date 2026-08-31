import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from models.cvdl_model import FloodNetUNet
from src.dataset import FloodNetDataset


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# SETTINGS
# ============================================================

NUM_CLASSES = 10

IMAGE_SIZE = (512, 512)

BATCH_SIZE = 4

NUM_WORKERS = 0


# ============================================================
# DATASET PATH
# ============================================================

DATASET_ROOT = Path(
    "/Users/rifa/Downloads/FloodNet-Supervised_v1"
)

VAL_IMAGE_DIR = DATASET_ROOT / "val" / "val-org-img"

VAL_MASK_DIR = DATASET_ROOT / "val" / "val-label-img"


# ============================================================
# MODEL PATH
# ============================================================

MODEL_PATH = (
    PROJECT_ROOT /
    "outputs" /
    "best_model_weighted.pth"
)


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
# DEVICE
# ============================================================

if torch.backends.mps.is_available():

    device = torch.device("mps")

elif torch.cuda.is_available():

    device = torch.device("cuda")

else:

    device = torch.device("cpu")


print("=" * 70)
print("CVDL FULL VALIDATION EVALUATION")
print("=" * 70)

print("Device:", device)


# ============================================================
# DATASET
# ============================================================

print("\nLoading validation dataset...")

val_dataset = FloodNetDataset(
    image_dir=VAL_IMAGE_DIR,
    mask_dir=VAL_MASK_DIR,
    image_size=IMAGE_SIZE
)

print("Validation images:", len(val_dataset))


# ============================================================
# DATALOADER
# ============================================================

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=False
)

print("Validation batches:", len(val_loader))


# ============================================================
# MODEL
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

# Your training code saves a checkpoint dictionary.
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
# CONFUSION MATRIX
# ============================================================

confusion_matrix = np.zeros(
    (
        NUM_CLASSES,
        NUM_CLASSES
    ),
    dtype=np.int64
)


# ============================================================
# EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("RUNNING FULL VALIDATION")
print("=" * 70)

total_correct = 0
total_pixels = 0

processed_images = 0


with torch.no_grad():

    for batch_idx, (images, masks) in enumerate(val_loader):

        images = images.to(
            device,
            non_blocking=True
        )

        masks = masks.to(
            device,
            non_blocking=True
        )

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        outputs = model(images)

        predictions = torch.argmax(
            outputs,
            dim=1
        )


        # ----------------------------------------------------
        # Pixel Accuracy
        # ----------------------------------------------------

        total_correct += (
            predictions == masks
        ).sum().item()

        total_pixels += masks.numel()


        # ----------------------------------------------------
        # Confusion Matrix
        # ----------------------------------------------------

        true_pixels = (
            masks
            .cpu()
            .numpy()
            .reshape(-1)
        )

        predicted_pixels = (
            predictions
            .cpu()
            .numpy()
            .reshape(-1)
        )


        for true_class, predicted_class in zip(
            true_pixels,
            predicted_pixels
        ):

            if (
                0 <= true_class < NUM_CLASSES
                and
                0 <= predicted_class < NUM_CLASSES
            ):

                confusion_matrix[
                    true_class,
                    predicted_class
                ] += 1


        processed_images += images.shape[0]


        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if (
            batch_idx + 1
        ) % 10 == 0:

            print(
                f"Processed "
                f"{processed_images}/"
                f"{len(val_dataset)} images"
            )


# ============================================================
# PIXEL ACCURACY
# ============================================================

pixel_accuracy = (
    total_correct /
    total_pixels
)


# ============================================================
# PER-CLASS IoU
# ============================================================

class_iou = []


for class_id in range(NUM_CLASSES):

    true_positive = confusion_matrix[
        class_id,
        class_id
    ]

    false_positive = (
        confusion_matrix[
            :,
            class_id
        ].sum()
        -
        true_positive
    )

    false_negative = (
        confusion_matrix[
            class_id,
            :
        ].sum()
        -
        true_positive
    )

    denominator = (
        true_positive
        +
        false_positive
        +
        false_negative
    )

    if denominator == 0:

        iou = float("nan")

    else:

        iou = (
            true_positive /
            denominator
        )

    class_iou.append(iou)


# ============================================================
# FOREGROUND mIoU
# ============================================================

valid_ious = [
    class_iou[class_id]
    for class_id in range(
        1,
        NUM_CLASSES
    )
    if not np.isnan(
        class_iou[class_id]
    )
]


foreground_miou = np.mean(
    valid_ious
)


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n")
print("=" * 70)
print("FULL VALIDATION RESULTS")
print("=" * 70)

print(
    f"Images evaluated : {processed_images}"
)

print(
    f"Pixel Accuracy   : "
    f"{pixel_accuracy:.4f}"
)

print(
    f"Foreground mIoU  : "
    f"{foreground_miou:.4f}"
)


# ============================================================
# PER-CLASS RESULTS
# ============================================================

print("\nPer-Class IoU:")
print("-" * 70)


for class_id in range(NUM_CLASSES):

    if np.isnan(
        class_iou[class_id]
    ):

        iou_text = "N/A"

    else:

        iou_text = (
            f"{class_iou[class_id]:.4f}"
        )

    print(
        f"Class {class_id} "
        f"({CLASS_NAMES[class_id]:25s}) "
        f": {iou_text}"
    )


# ============================================================
# FLOODED CLASS PERFORMANCE
# ============================================================

flooded_classes = [
    1,
    3
]

flooded_ious = [
    class_iou[class_id]
    for class_id in flooded_classes
    if not np.isnan(
        class_iou[class_id]
    )
]


if len(flooded_ious) > 0:

    flooded_miou = np.mean(
        flooded_ious
    )

else:

    flooded_miou = float("nan")


print("\n" + "-" * 70)

print(
    f"Flooded Classes mIoU : "
    f"{flooded_miou:.4f}"
)


# ============================================================
# NON-FLOODED CLASS PERFORMANCE
# ============================================================

non_flooded_classes = [
    2,
    4
]

non_flooded_ious = [
    class_iou[class_id]
    for class_id in non_flooded_classes
    if not np.isnan(
        class_iou[class_id]
    )
]


if len(non_flooded_ious) > 0:

    non_flooded_miou = np.mean(
        non_flooded_ious
    )

else:

    non_flooded_miou = float("nan")


print(
    f"Non-Flooded Classes mIoU : "
    f"{non_flooded_miou:.4f}"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\n" + "=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print(
    confusion_matrix
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("FULL VALIDATION EVALUATION COMPLETE")
print("=" * 70)