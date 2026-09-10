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

# Only 10 additional fine-tuning epochs
NUM_EPOCHS = 10

BATCH_SIZE = 4

# Fresh optimizer will actually use this LR
LEARNING_RATE = 5e-5

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
# MODEL NAME
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

# Stronger focus on actual flooded classes.
#
# Road-Flooded gets the highest weight because it was
# the weakest class in the previous evaluation.
#
# Building-Flooded and Water are also given strong weights.

CLASS_WEIGHTS = torch.tensor(
    [
        0.35,  # 0 Background
        2.50,  # 1 Building-Flooded
        1.10,  # 2 Building-Non-Flooded
        3.50,  # 3 Road-Flooded
        1.10,  # 4 Road-Non-Flooded
        1.50,  # 5 Water
        1.00,  # 6 Tree
        1.50,  # 7 Vehicle
        0.75,  # 8 Pool
        1.00   # 9 Grass
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
# FLOOD-FOCUSED DICE LOSS
# ============================================================

def dice_loss(
    probabilities,
    masks,
    num_classes
):

    masks_one_hot = torch.nn.functional.one_hot(
        masks.long(),
        num_classes=num_classes
    )


    masks_one_hot = masks_one_hot.permute(
        0,
        3,
        1,
        2
    ).float()


    smooth = 1e-6

    dice_total = 0.0

    weight_total = 0.0


    # Stronger importance for flooded classes.

    dice_weights = torch.tensor(
        [
            0.0,  # Background
            2.5,  # Building-Flooded
            1.0,  # Building-Non-Flooded
            3.5,  # Road-Flooded
            1.5,  # Road-Non-Flooded
            1.8,  # Water
            1.0,  # Tree
            1.2,  # Vehicle
            0.5,  # Pool
            1.0   # Grass
        ],
        dtype=probabilities.dtype,
        device=probabilities.device
    )


    for class_id in range(num_classes):

        if dice_weights[class_id].item() == 0:

            continue


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
            dice_weights[class_id]
            *
            (1.0 - dice)
        )


        weight_total += dice_weights[class_id]


    return dice_total / weight_total


# ============================================================
# TVERSKY LOSS
# ============================================================

def tversky_loss(
    probabilities,
    masks,
    num_classes,
    alpha=0.7,
    beta=0.3
):

    masks_one_hot = torch.nn.functional.one_hot(
        masks.long(),
        num_classes=num_classes
    )


    masks_one_hot = masks_one_hot.permute(
        0,
        3,
        1,
        2
    ).float()


    smooth = 1e-6

    total_loss = 0.0

    total_weight = 0.0


    # Road-Flooded receives strongest focus.
    #
    # alpha > beta means false negatives are penalized more.
    #
    # This is useful when the model is missing actual
    # flooded-road pixels.

    tversky_weights = torch.tensor(
        [
            0.0,  # Background
            2.5,  # Building-Flooded
            1.0,  # Building-Non-Flooded
            4.0,  # Road-Flooded
            1.0,  # Road-Non-Flooded
            1.5,  # Water
            1.0,  # Tree
            1.2,  # Vehicle
            0.5,  # Pool
            1.0   # Grass
        ],
        dtype=probabilities.dtype,
        device=probabilities.device
    )


    for class_id in range(num_classes):

        if tversky_weights[class_id].item() == 0:

            continue


        predicted = probabilities[
            :,
            class_id
        ]


        actual = masks_one_hot[
            :,
            class_id
        ]


        true_positive = (
            predicted * actual
        ).sum()


        false_negative = (
            (1.0 - predicted) * actual
        ).sum()


        false_positive = (
            predicted * (1.0 - actual)
        ).sum()


        tversky = (
            true_positive
            +
            smooth
        ) / (
            true_positive
            +
            alpha * false_negative
            +
            beta * false_positive
            +
            smooth
        )


        total_loss += (
            tversky_weights[class_id]
            *
            (1.0 - tversky)
        )


        total_weight += (
            tversky_weights[class_id]
        )


    return total_loss / total_weight


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
    # Probabilities
    # --------------------------------------------------------

    probabilities = torch.softmax(
        outputs,
        dim=1
    )


    # --------------------------------------------------------
    # Flood-focused Dice
    # --------------------------------------------------------

    dice = dice_loss(
        probabilities,
        masks,
        NUM_CLASSES
    )


    # --------------------------------------------------------
    # Tversky
    # --------------------------------------------------------

    tversky = tversky_loss(
        probabilities,
        masks,
        NUM_CLASSES
    )


    # --------------------------------------------------------
    # Combined
    # --------------------------------------------------------

    return (
        0.40 * ce
        +
        0.25 * dice
        +
        0.35 * tversky
    )


# ============================================================
# OPTIMIZER
# ============================================================

# IMPORTANT:
# We intentionally create a FRESH optimizer.
#
# We do NOT load the old optimizer state.
# Therefore LEARNING_RATE = 5e-5 will actually be used.

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=1e-5
)


# ============================================================
# LEARNING RATE SCHEDULER
# ============================================================

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=2
)


# ============================================================
# RESUME MODEL WEIGHTS ONLY
# ============================================================

start_epoch = 0

best_miou = -1.0

best_flooded_miou = -1.0


if BEST_MODEL_PATH.exists():

    print("\n" + "=" * 70)
    print("LOADING CURRENT BEST MODEL")
    print("=" * 70)


    checkpoint = torch.load(
        BEST_MODEL_PATH,
        map_location=device,
        weights_only=False
    )


    if "model_state_dict" in checkpoint:

        model.load_state_dict(
            checkpoint["model_state_dict"]
        )


        start_epoch = int(
            checkpoint.get(
                "epoch",
                0
            )
        )


        best_miou = float(
            checkpoint.get(
                "best_miou",
                -1.0
            )
        )


        # ----------------------------------------------------
        # Get previous flooded mIoU from checkpoint
        # ----------------------------------------------------

        previous_class_iou = checkpoint.get(
            "class_iou",
            None
        )


        if previous_class_iou is not None:

            try:

                previous_flooded_values = [

                    float(previous_class_iou[1]),
                    float(previous_class_iou[3])

                ]


                previous_flooded_values = [

                    value

                    for value in previous_flooded_values

                    if not np.isnan(value)

                ]


                if previous_flooded_values:

                    best_flooded_miou = float(
                        np.mean(
                            previous_flooded_values
                        )
                    )

            except Exception:

                best_flooded_miou = -1.0


    else:

        model.load_state_dict(
            checkpoint
        )


    print(
        "Resumed model from epoch:",
        start_epoch
    )


    print(
        "Previous overall best mIoU:",
        best_miou
    )


    print(
        "Previous flooded mIoU:",
        best_flooded_miou
    )


else:

    print(
        "\nNo existing checkpoint found."
    )


# ============================================================
# DATA AUGMENTATION
# ============================================================

def augment_batch(
    images,
    masks
):

    # --------------------------------------------------------
    # Horizontal flip
    # --------------------------------------------------------

    if torch.rand(1).item() < 0.5:

        images = torch.flip(
            images,
            dims=[3]
        )


        masks = torch.flip(
            masks,
            dims=[2]
        )


    # --------------------------------------------------------
    # Vertical flip
    # --------------------------------------------------------

    if torch.rand(1).item() < 0.5:

        images = torch.flip(
            images,
            dims=[2]
        )


        masks = torch.flip(
            masks,
            dims=[1]
        )


    # --------------------------------------------------------
    # 90-degree rotation
    # --------------------------------------------------------

    if torch.rand(1).item() < 0.5:

        k = int(
            torch.randint(
                1,
                4,
                (1,)
            ).item()
        )


        images = torch.rot90(
            images,
            k=k,
            dims=[2, 3]
        )


        masks = torch.rot90(
            masks,
            k=k,
            dims=[1, 2]
        )


    return images, masks


# ============================================================
# VALIDATION FUNCTION
# ============================================================

def validate():

    model.eval()


    total_correct = 0

    total_pixels = 0


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
            ).long()


            # ------------------------------------------------
            # Prediction
            # ------------------------------------------------

            outputs = model(
                images
            )


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


            total_pixels += (
                masks.numel()
            )


            # ------------------------------------------------
            # Confusion matrix
            # ------------------------------------------------

            true_pixels = (
                masks.cpu()
                .numpy()
                .reshape(-1)
            )


            predicted_pixels = (
                predictions.cpu()
                .numpy()
                .reshape(-1)
            )


            valid = (
                (true_pixels >= 0)
                &
                (true_pixels < NUM_CLASSES)
                &
                (predicted_pixels >= 0)
                &
                (predicted_pixels < NUM_CLASSES)
            )


            confusion_matrix += np.bincount(
                NUM_CLASSES * true_pixels[valid]
                +
                predicted_pixels[valid],
                minlength=(
                    NUM_CLASSES
                    *
                    NUM_CLASSES
                )
            ).reshape(
                NUM_CLASSES,
                NUM_CLASSES
            )


    # ========================================================
    # PIXEL ACCURACY
    # ========================================================

    pixel_accuracy = (
        total_correct
        /
        max(total_pixels, 1)
    )


    # ========================================================
    # PER CLASS IoU
    # ========================================================

    class_iou = []


    for class_id in range(
        NUM_CLASSES
    ):

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


        class_iou.append(
            iou
        )


    # ========================================================
    # OVERALL MEAN IoU
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


    # ========================================================
    # FLOODED CLASSES
    # ========================================================

    flooded_iou_values = [

        class_iou[1],
        class_iou[3]

    ]


    flooded_iou_values = [

        value

        for value in flooded_iou_values

        if not np.isnan(value)

    ]


    if flooded_iou_values:

        flooded_mean_iou = np.mean(
            flooded_iou_values
        )

    else:

        flooded_mean_iou = 0.0


    return (
        pixel_accuracy,
        mean_iou,
        flooded_mean_iou,
        class_iou,
        confusion_matrix
    )


# ============================================================
# TRAINING
# ============================================================

print("\n" + "=" * 70)
print("STARTING FLOOD-FOCUSED FINE-TUNING")
print("=" * 70)


print(
    f"Additional epochs : "
    f"{NUM_EPOCHS}"
)


print(
    f"Batch size        : "
    f"{BATCH_SIZE}"
)


print(
    f"Image size        : "
    f"{IMAGE_SIZE}"
)


print(
    f"Learning rate     : "
    f"{LEARNING_RATE}"
)


print(
    "Loss              : "
    "Weighted CE + Flood Dice + Tversky"
)


print(
    "Augmentation      : "
    "Horizontal/Vertical Flip + 90° Rotation"
)


print(
    "Checkpoint metric : "
    "Flooded Classes mIoU"
)


print("=" * 70)


# ============================================================
# EPOCH LOOP
# ============================================================

for epoch in range(
    start_epoch,
    start_epoch + NUM_EPOCHS
):

    # ========================================================
    # TRAIN MODE
    # ========================================================

    model.train()


    total_train_loss = 0.0


    print("\n" + "=" * 70)


    print(
        f"Epoch "
        f"{epoch + 1}/"
        f"{start_epoch + NUM_EPOCHS}"
    )


    print("=" * 70)


    # ========================================================
    # BATCH LOOP
    # ========================================================

    for batch_idx, (
        images,
        masks
    ) in enumerate(
        train_loader
    ):


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
        ).long()


        # ----------------------------------------------------
        # Augmentation
        # ----------------------------------------------------

        images, masks = augment_batch(
            images,
            masks
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
        # Gradient clipping
        # ----------------------------------------------------

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=1.0
        )


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
        # Print progress
        # ----------------------------------------------------

        if (
            batch_idx + 1
        ) % 100 == 0:

            print(
                f"Batch "
                f"{batch_idx + 1}/"
                f"{len(train_loader)} "
                f"| Loss: "
                f"{loss.item():.4f}"
            )


    # ========================================================
    # AVERAGE TRAIN LOSS
    # ========================================================

    average_train_loss = (
        total_train_loss
        /
        max(
            len(train_loader),
            1
        )
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    (
        pixel_accuracy,
        mean_iou,
        flooded_mean_iou,
        class_iou,
        confusion_matrix
    ) = validate()


    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print(
        "\n"
        +
        "-" * 70
    )


    print(
        f"Epoch "
        f"{epoch + 1}"
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


    print(
        f"Flooded mIoU   : "
        f"{flooded_mean_iou:.4f}"
    )


    # ========================================================
    # PER CLASS IoU
    # ========================================================

    print(
        "\nPer-class IoU:"
    )


    for class_id in range(
        NUM_CLASSES
    ):


        if np.isnan(
            class_iou[class_id]
        ):

            iou_text = "N/A"

        else:

            iou_text = (
                f"{class_iou[class_id]:.4f}"
            )


        print(
            f"Class "
            f"{class_id} "
            f"("
            f"{CLASS_NAMES[class_id]:25s}"
            f") "
            f": "
            f"{iou_text}"
        )


    # ========================================================
    # FLOODED CLASS DETAILS
    # ========================================================

    print(
        "\nFlood-focused results:"
    )


    print(
        f"Building-Flooded : "
        f"{class_iou[1]:.4f}"
    )


    print(
        f"Road-Flooded     : "
        f"{class_iou[3]:.4f}"
    )


    print(
        f"Water            : "
        f"{class_iou[5]:.4f}"
    )


    print(
        f"Vehicle          : "
        f"{class_iou[7]:.4f}"
    )


    # ========================================================
    # LEARNING RATE SCHEDULER
    # ========================================================

    scheduler.step(
        flooded_mean_iou
    )


    current_lr = optimizer.param_groups[0]["lr"]


    print(
        f"\nLearning Rate: "
        f"{current_lr:.2e}"
    )


    # ========================================================
    # SAVE BEST FLOODED MODEL
    # ========================================================

    if flooded_mean_iou > best_flooded_miou:

        best_flooded_miou = flooded_mean_iou

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

            "best_flooded_miou":
                best_flooded_miou,

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
            "\nBEST FLOODED MODEL SAVED!"
        )


        print(
            f"Best flooded mIoU: "
            f"{best_flooded_miou:.4f}"
        )


        print(
            f"Overall mIoU: "
            f"{best_miou:.4f}"
        )


        print(
            f"Saved to: "
            f"{BEST_MODEL_PATH}"
        )


    else:

        print(
            "\nNo improvement in flooded mIoU."
        )


# ============================================================
# TRAINING COMPLETE
# ============================================================

print("\n")


print(
    "=" * 70
)


print(
    "FLOOD-FOCUSED TRAINING COMPLETE"
)


print(
    "=" * 70
)


print(
    f"Best Flooded mIoU: "
    f"{best_flooded_miou:.4f}"
)


print(
    f"Best Overall mIoU: "
    f"{best_miou:.4f}"
)


print(
    "Best model:"
)


print(
    BEST_MODEL_PATH
)


print(
    "=" * 70
)