import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS FROM YOUR PROJECT
# ============================================================

from models.cvdl_model import FloodNetUNet
from src.dataset import FloodNetDataset


# ============================================================
# SETTINGS
# ============================================================

NUM_CLASSES = 10

IMAGE_SIZE = (512, 512)

NUM_EPOCHS = 20

BATCH_SIZE = 4

LEARNING_RATE = 1e-4

NUM_WORKERS = 0


# ============================================================
# DATASET PATH
# ============================================================

DATASET_ROOT = Path(
    "/Users/rifa/Downloads/FloodNet-Supervised_v1"
)


TRAIN_IMAGE_DIR = DATASET_ROOT / "train" / "train-org-img"

TRAIN_MASK_DIR = DATASET_ROOT / "train" / "train-label-img"

VAL_IMAGE_DIR = DATASET_ROOT / "val" / "val-org-img"

VAL_MASK_DIR = DATASET_ROOT / "val" / "val-label-img"


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR = PROJECT_ROOT / "outputs"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# NEW MODEL NAME
# ============================================================

BEST_MODEL_PATH = OUTPUT_DIR / "best_model_weighted.pth"


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
print("DEVICE")
print("=" * 70)

print("Using device:", device)


# ============================================================
# DATASET
# ============================================================

print("\n" + "=" * 70)
print("LOADING DATASET")
print("=" * 70)


train_dataset = FloodNetDataset(
    image_dir=TRAIN_IMAGE_DIR,
    mask_dir=TRAIN_MASK_DIR,
    image_size=IMAGE_SIZE
)


val_dataset = FloodNetDataset(
    image_dir=VAL_IMAGE_DIR,
    mask_dir=VAL_MASK_DIR,
    image_size=IMAGE_SIZE
)


print("Training images:", len(train_dataset))

print("Validation images:", len(val_dataset))


# ============================================================
# DATALOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS,
    pin_memory=False
)


val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=False
)


print("Training batches:", len(train_loader))

print("Validation batches:", len(val_loader))


# ============================================================
# MODEL
# ============================================================

print("\n" + "=" * 70)
print("CREATING MODEL")
print("=" * 70)


model = FloodNetUNet(
    num_classes=NUM_CLASSES
)


model = model.to(device)


print("Model created successfully.")


# ============================================================
# CLASS WEIGHTS
# ============================================================

# We are NOT giving Grass a high weight because
# Grass prediction amount is already close to Ground Truth.
#
# We are increasing the importance of:
#
# Building-Flooded
# Road-Flooded
# Vehicle
# Pool
#
# Background is slightly reduced.

CLASS_WEIGHTS = torch.tensor(
    [
        0.5,   # 0 Background
        1.5,   # 1 Building-Flooded
        1.2,   # 2 Building-Non-Flooded
        1.5,   # 3 Road-Flooded
        1.2,   # 4 Road-Non-Flooded
        1.0,   # 5 Water
        1.0,   # 6 Tree
        2.0,   # 7 Vehicle
        2.0,   # 8 Pool
        1.0    # 9 Grass
    ],
    dtype=torch.float32
).to(device)


print("\nClass weights:")

for class_id in range(NUM_CLASSES):

    print(
        f"{class_id:2d} "
        f"{CLASS_NAMES[class_id]:25s} "
        f"{CLASS_WEIGHTS[class_id].item():.2f}"
    )


# ============================================================
# CROSS ENTROPY LOSS
# ============================================================

ce_loss_function = torch.nn.CrossEntropyLoss(
    weight=CLASS_WEIGHTS
)


# ============================================================
# DICE LOSS
# ============================================================

def dice_loss(
    probabilities,
    masks,
    num_classes
):

    """
    Multi-class Dice Loss.

    probabilities:
        [B, C, H, W]

    masks:
        [B, H, W]
    """

    # --------------------------------------------------------
    # One-hot encode ground truth
    # --------------------------------------------------------

    masks_one_hot = torch.nn.functional.one_hot(
        masks,
        num_classes=num_classes
    )

    # [B, H, W, C]
    # →
    # [B, C, H, W]

    masks_one_hot = masks_one_hot.permute(
        0,
        3,
        1,
        2
    ).float()


    smooth = 1e-6

    dice_total = 0.0


    # --------------------------------------------------------
    # Calculate Dice for every class
    # --------------------------------------------------------

    for class_id in range(num_classes):

        predicted = probabilities[
            :,
            class_id
        ]

        actual = masks_one_hot[
            :,
            class_id
        ]


        intersection = (
            predicted * actual
        ).sum()


        denominator = (
            predicted.sum()
            +
            actual.sum()
        )


        dice = (
            2.0 * intersection
            +
            smooth
        ) / (
            denominator
            +
            smooth
        )


        dice_total += (
            1.0 - dice
        )


    return dice_total / num_classes


# ============================================================
# COMBINED LOSS
# ============================================================

def combined_loss(
    outputs,
    masks
):

    # --------------------------------------------------------
    # Cross Entropy
    # --------------------------------------------------------

    ce = ce_loss_function(
        outputs,
        masks
    )


    # --------------------------------------------------------
    # Convert logits → probabilities
    # --------------------------------------------------------

    probabilities = torch.softmax(
        outputs,
        dim=1
    )


    # --------------------------------------------------------
    # Dice
    # --------------------------------------------------------

    dice = dice_loss(
        probabilities,
        masks,
        NUM_CLASSES
    )


    # --------------------------------------------------------
    # Combined
    # --------------------------------------------------------

    return ce + dice


# ============================================================
# OPTIMIZER
# ============================================================

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)


# ============================================================
# LEARNING RATE SCHEDULER
# ============================================================

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=3
)


# ============================================================
# VALIDATION FUNCTION
# ============================================================

def validate():

    model.eval()


    total_correct = 0

    total_pixels = 0


    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    confusion_matrix = np.zeros(
        (
            NUM_CLASSES,
            NUM_CLASSES
        ),
        dtype=np.int64
    )


    with torch.no_grad():

        for images, masks in val_loader:

            images = images.to(
                device,
                non_blocking=True
            )

            masks = masks.to(
                device,
                non_blocking=True
            )


            # ------------------------------------------------
            # Prediction
            # ------------------------------------------------

            outputs = model(images)


            predictions = torch.argmax(
                outputs,
                dim=1
            )


            # ------------------------------------------------
            # Pixel accuracy
            # ------------------------------------------------

            total_correct += (
                predictions == masks
            ).sum().item()


            total_pixels += masks.numel()


            # ------------------------------------------------
            # Confusion matrix
            # ------------------------------------------------

            true_pixels = masks.cpu().numpy().reshape(-1)

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


    # ========================================================
    # Pixel Accuracy
    # ========================================================

    pixel_accuracy = (
        total_correct / total_pixels
    )


    # ========================================================
    # PER CLASS IoU
    # ========================================================

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
                true_positive
                /
                denominator
            )


        class_iou.append(iou)


    # ========================================================
    # MEAN IoU
    # ========================================================
    #
    # IMPORTANT:
    # Background (class 0) is excluded.
    #
    # This matches your previous analysis where
    # Background IoU was 0.0000.
    #
    # ========================================================

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


    mean_iou = np.mean(
        valid_ious
    )


    return (
        pixel_accuracy,
        mean_iou,
        class_iou,
        confusion_matrix
    )


# ============================================================
# TRAINING
# ============================================================

print("\n" + "=" * 70)
print("STARTING TRAINING")
print("=" * 70)

print(
    f"Epochs      : {NUM_EPOCHS}"
)

print(
    f"Batch size  : {BATCH_SIZE}"
)

print(
    f"Image size  : {IMAGE_SIZE}"
)

print(
    f"Learning rate: {LEARNING_RATE}"
)

print(
    "Loss        : Weighted CE + Dice"
)

print("=" * 70)


best_miou = -1.0


# ============================================================
# EPOCH LOOP
# ============================================================

for epoch in range(NUM_EPOCHS):


    # ========================================================
    # TRAIN MODE
    # ========================================================

    model.train()


    total_train_loss = 0.0


    print("\n")
    print("=" * 70)

    print(
        f"Epoch {epoch + 1}/{NUM_EPOCHS}"
    )

    print("=" * 70)


    # ========================================================
    # BATCH LOOP
    # ========================================================

    for batch_idx, (
        images,
        masks
    ) in enumerate(train_loader):


        # ----------------------------------------------------
        # Move data to device
        # ----------------------------------------------------

        images = images.to(
            device,
            non_blocking=True
        )

        masks = masks.to(
            device,
            non_blocking=True
        )


        # ----------------------------------------------------
        # Clear gradients
        # ----------------------------------------------------

        optimizer.zero_grad(
            set_to_none=True
        )


        # ----------------------------------------------------
        # Forward pass
        # ----------------------------------------------------

        outputs = model(
            images
        )


        # ----------------------------------------------------
        # Loss
        # ----------------------------------------------------

        loss = combined_loss(
            outputs,
            masks
        )


        # ----------------------------------------------------
        # Backward pass
        # ----------------------------------------------------

        loss.backward()


        # ----------------------------------------------------
        # Update weights
        # ----------------------------------------------------

        optimizer.step()


        # ----------------------------------------------------
        # Store loss
        # ----------------------------------------------------

        total_train_loss += (
            loss.item()
        )


        # ----------------------------------------------------
        # Print every 100 batches
        # ----------------------------------------------------

        if (
            batch_idx + 1
        ) % 100 == 0:

            print(
                f"Batch "
                f"{batch_idx + 1}"
                f"/{len(train_loader)} "
                f"| Loss: "
                f"{loss.item():.4f}"
            )


    # ========================================================
    # AVERAGE TRAIN LOSS
    # ========================================================

    average_train_loss = (
        total_train_loss
        /
        len(train_loader)
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    (
        pixel_accuracy,
        mean_iou,
        class_iou,
        confusion_matrix
    ) = validate()


    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print("\n" + "-" * 70)

    print(
        f"Epoch {epoch + 1}/{NUM_EPOCHS}"
    )

    print(
        f"Train Loss     : "
        f"{average_train_loss:.4f}"
    )

    print(
        f"Pixel Accuracy : "
        f"{pixel_accuracy:.4f}"
    )

    print(
        f"Mean IoU       : "
        f"{mean_iou:.4f}"
    )


    # ========================================================
    # PER CLASS IoU
    # ========================================================

    print("\nPer-class IoU:")

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


    # ========================================================
    # LEARNING RATE SCHEDULER
    # ========================================================

    scheduler.step(
        mean_iou
    )


    current_lr = optimizer.param_groups[0]["lr"]

    print(
        f"\nLearning Rate: "
        f"{current_lr:.2e}"
    )


    # ========================================================
    # SAVE BEST MODEL
    # ========================================================

    if mean_iou > best_miou:

        best_miou = mean_iou


        checkpoint = {

            "epoch":
                epoch + 1,

            "model_state_dict":
                model.state_dict(),

            "optimizer_state_dict":
                optimizer.state_dict(),

            "best_miou":
                best_miou,

            "pixel_accuracy":
                pixel_accuracy,

            "class_iou":
                class_iou

        }


        torch.save(
            checkpoint,
            BEST_MODEL_PATH
        )


        print(
            "\nBEST MODEL SAVED!"
        )

        print(
            f"Best mIoU: "
            f"{best_miou:.4f}"
        )

        print(
            f"Saved to: "
            f"{BEST_MODEL_PATH}"
        )

    else:

        print(
            "\nNo improvement in mIoU."
        )


# ============================================================
# TRAINING COMPLETE
# ============================================================

print("\n")
print("=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)

print(
    f"Best Validation mIoU: "
    f"{best_miou:.4f}"
)

print(
    f"Best model:"
)

print(
    BEST_MODEL_PATH
)

print("=" * 70)