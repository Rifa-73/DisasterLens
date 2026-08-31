import torch
import numpy as np
from PIL import Image
from pathlib import Path
import matplotlib.pyplot as plt
import sys


# ==========================================
# PROJECT ROOT
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from models.cvdl_model import FloodNetUNet


# ==========================================
# SETTINGS
# ==========================================

MAX_IMAGES = 20

NUM_CLASSES = 10

# MUST MATCH train.py
IMAGE_SIZE = (512, 512)

MODEL_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "best_model_weighted.pth"
)


# ==========================================
# IMAGE + MASK DIRECTORIES
# ==========================================

IMAGE_DIR = Path(
    "/Users/rifa/Downloads/FloodNet-Supervised_v1/val/val-org-img"
)

MASK_DIR = Path(
    "/Users/rifa/Downloads/FloodNet-Supervised_v1/val/val-label-img"
)


# ==========================================
# CLASS NAMES
# ==========================================

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


# ==========================================
# DEVICE
# ==========================================

if torch.backends.mps.is_available():

    device = torch.device("mps")

elif torch.cuda.is_available():

    device = torch.device("cuda")

else:

    device = torch.device("cpu")


print("=" * 60)
print("FLOODNET PREDICTION")
print("=" * 60)

print("Device:", device)


# ==========================================
# LOAD MODEL
# ==========================================

print("\nLoading model...")

model = FloodNetUNet(
    num_classes=NUM_CLASSES
)


checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
    weights_only=False
)


# Your train.py saves a dictionary
if (
    isinstance(checkpoint, dict)
    and "model_state_dict" in checkpoint
):

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

else:

    model.load_state_dict(
        checkpoint
    )


model = model.to(device)

model.eval()


print("Model loaded successfully!")

print(
    "Model:",
    MODEL_PATH
)


# ==========================================
# FIND VALIDATION IMAGES
# ==========================================

image_files = sorted(
    list(IMAGE_DIR.glob("*.jpg")) +
    list(IMAGE_DIR.glob("*.png")) +
    list(IMAGE_DIR.glob("*.jpeg"))
)

if len(image_files) == 0:

    raise FileNotFoundError(
        f"No images found in:\n{IMAGE_DIR}"
    )


# Take only MAX_IMAGES
image_files = image_files[:MAX_IMAGES]


print(
    "\nValidation images found:",
    len(image_files)
)

print(
    f"Running prediction on first {len(image_files)} images..."
)


# ==========================================
# OUTPUT DIRECTORY
# ==========================================

output_dir = (
    PROJECT_ROOT
    / "outputs"
)

output_dir.mkdir(
    exist_ok=True
)


# ==========================================
# COLOUR MAP
# ==========================================

COLORS = np.array([
    [0,   0,   0],       # Background
    [255, 0,   0],       # Building-Flooded
    [255, 128, 0],       # Building-Non-Flooded
    [0,   0,   255],     # Road-Flooded
    [128, 128, 128],     # Road-Non-Flooded
    [0,   255, 255],     # Water
    [0,   128, 0],       # Tree
    [255, 255, 0],       # Vehicle
    [128, 0,   255],     # Pool
    [0,   255, 0]        # Grass
], dtype=np.uint8)


# ==========================================
# PROCESS IMAGES
# ==========================================

all_pixel_accuracies = []

all_foreground_mious = []

all_class_ious = [
    []
    for _ in range(NUM_CLASSES)
]


for image_number, image_path in enumerate(
    image_files,
    start=1
):

    print("\n")
    print("=" * 60)

    print(
        f"IMAGE {image_number}/{len(image_files)}"
    )

    print("=" * 60)

    print(
        "Testing image:",
        image_path
    )


    # ======================================
    # FIND CORRESPONDING MASK
    # ======================================

    image_name = image_path.stem

    mask_path = (
        MASK_DIR
        / f"{image_name}_lab.png"
    )


    if not mask_path.exists():

        print(
            "Ground-truth mask not found:"
        )

        print(mask_path)

        print(
            "Skipping this image..."
        )

        continue


    print(
        "\nGround-truth mask:"
    )

    print(mask_path)


    # ======================================
    # LOAD ORIGINAL IMAGE
    # ======================================

    original_image = Image.open(
        image_path
    ).convert("RGB")


    print(
        "\nOriginal image size:",
        original_image.size
    )


    # ======================================
    # LOAD GROUND TRUTH MASK
    # ======================================

    ground_truth = Image.open(
        mask_path
    ).convert("L")


    print(
        "Original mask size:",
        ground_truth.size
    )


    # ======================================
    # PREPROCESS IMAGE
    # EXACTLY LIKE dataset.py
    # ======================================

    image = original_image.resize(
        IMAGE_SIZE,
        Image.Resampling.BILINEAR
    )


    image_np = np.array(
        image,
        dtype=np.float32
    ) / 255.0


    # HWC → CHW

    image_tensor = torch.from_numpy(
        image_np
    ).permute(
        2,
        0,
        1
    )


    # Add batch dimension

    image_tensor = image_tensor.unsqueeze(
        0
    )


    image_tensor = image_tensor.to(
        device
    )


    # ======================================
    # PREPROCESS GROUND TRUTH
    # EXACTLY LIKE dataset.py
    # ======================================

    ground_truth = ground_truth.resize(
        IMAGE_SIZE,
        Image.Resampling.NEAREST
    )


    ground_truth = np.array(
        ground_truth,
        dtype=np.int64
    )


    # ======================================
    # RUN MODEL
    # ======================================

    print(
        "\nRunning prediction..."
    )


    with torch.no_grad():

        output = model(
            image_tensor
        )


    print(
        "Raw output shape:",
        tuple(output.shape)
    )


    # ======================================
    # ARGMAX
    # ======================================

    prediction = torch.argmax(
        output,
        dim=1
    )


    # [1,H,W] → [H,W]

    prediction = prediction.squeeze(
        0
    )


    prediction = (
        prediction
        .cpu()
        .numpy()
        .astype(np.uint8)
    )


    print(
        "Prediction shape:",
        prediction.shape
    )


    # ======================================
    # CHECK CLASSES
    # ======================================

    gt_classes = np.unique(
        ground_truth
    )

    pred_classes = np.unique(
        prediction
    )


    print(
        "\n" + "=" * 60
    )

    print(
        "GROUND TRUTH CLASSES"
    )

    print(
        "=" * 60
    )


    for class_id in gt_classes:

        count = np.sum(
            ground_truth == class_id
        )


        percentage = (
            count /
            ground_truth.size
        ) * 100


        print(
            f"Class {class_id:2d} "
            f"({CLASS_NAMES.get(class_id, 'Unknown'):22s}) : "
            f"{count:8,d} pixels "
            f"({percentage:6.2f}%)"
        )


    print(
        "\n" + "=" * 60
    )

    print(
        "PREDICTED CLASSES"
    )

    print(
        "=" * 60
    )


    for class_id in pred_classes:

        count = np.sum(
            prediction == class_id
        )


        percentage = (
            count /
            prediction.size
        ) * 100


        print(
            f"Class {class_id:2d} "
            f"({CLASS_NAMES.get(class_id, 'Unknown'):22s}) : "
            f"{count:8,d} pixels "
            f"({percentage:6.2f}%)"
        )


    # ======================================
    # PIXEL ACCURACY
    # ======================================

    pixel_accuracy = (
        prediction == ground_truth
    ).mean()


    all_pixel_accuracies.append(
        pixel_accuracy
    )


    print(
        "\n" + "=" * 60
    )

    print(
        f"Pixel Accuracy on this image: "
        f"{pixel_accuracy:.4f}"
    )

    print(
        "=" * 60
    )


    # ======================================
    # PER-CLASS IoU
    # ======================================

    print(
        "\nPer-class IoU for this image:"
    )


    per_class_iou = []


    for class_id in range(
        NUM_CLASSES
    ):

        intersection = np.logical_and(
            prediction == class_id,
            ground_truth == class_id
        ).sum()


        union = np.logical_or(
            prediction == class_id,
            ground_truth == class_id
        ).sum()


        if union == 0:

            iou = None

        else:

            iou = (
                intersection /
                union
            )


        per_class_iou.append(
            iou
        )


        if iou is None:

            print(
                f"{class_id:2d} "
                f"{CLASS_NAMES[class_id]:22s} "
                f": N/A"
            )

        else:

            print(
                f"{class_id:2d} "
                f"{CLASS_NAMES[class_id]:22s} "
                f": {iou:.4f}"
            )

            all_class_ious[
                class_id
            ].append(iou)


    # ======================================
    # FOREGROUND mIoU
    # EXCLUDE BACKGROUND
    # ======================================

    valid_ious = [
        iou

        for class_id, iou in enumerate(
            per_class_iou
        )

        if (
            iou is not None
            and
            class_id != 0
        )
    ]


    if len(valid_ious) > 0:

        foreground_miou = (
            sum(valid_ious)
            /
            len(valid_ious)
        )

    else:

        foreground_miou = 0.0


    all_foreground_mious.append(
        foreground_miou
    )


    print(
        "\nForeground mIoU "
        "(Background excluded): "
        f"{foreground_miou:.4f}"
    )


    # ======================================
    # SAVE RAW PREDICTION MASK
    # ======================================

    mask_output_path = (
        output_dir
        / f"{image_name}_prediction_mask.png"
    )


    Image.fromarray(
        prediction
    ).save(
        mask_output_path
    )


    print(
        "\nPrediction mask saved:"
    )

    print(
        mask_output_path
    )


    # ======================================
    # CREATE COLOURED GROUND TRUTH
    # ======================================

    ground_truth_color = np.zeros(
        (
            ground_truth.shape[0],
            ground_truth.shape[1],
            3
        ),
        dtype=np.uint8
    )


    for class_id in range(
        NUM_CLASSES
    ):

        ground_truth_color[
            ground_truth == class_id
        ] = COLORS[class_id]


    # ======================================
    # CREATE COLOURED PREDICTION
    # ======================================

    prediction_color = np.zeros(
        (
            prediction.shape[0],
            prediction.shape[1],
            3
        ),
        dtype=np.uint8
    )


    for class_id in range(
        NUM_CLASSES
    ):

        prediction_color[
            prediction == class_id
        ] = COLORS[class_id]


    # ======================================
    # RESIZE MASKS TO ORIGINAL IMAGE SIZE
    # ======================================

    ground_truth_display = Image.fromarray(
        ground_truth_color
    ).resize(
        original_image.size,
        Image.Resampling.NEAREST
    )


    prediction_display = Image.fromarray(
        prediction_color
    ).resize(
        original_image.size,
        Image.Resampling.NEAREST
    )


    # ======================================
    # VISUALIZATION
    # ======================================

    plt.figure(
        figsize=(20, 5)
    )


    # --------------------------------------
    # 1. ORIGINAL
    # --------------------------------------

    plt.subplot(
        1, 4, 1
    )


    plt.imshow(
        original_image
    )


    plt.title(
        "Original"
    )


    plt.axis(
        "off"
    )


    # --------------------------------------
    # 2. GROUND TRUTH
    # --------------------------------------

    plt.subplot(
        1, 4, 2
    )


    plt.imshow(
        ground_truth_display
    )


    plt.title(
        "Ground Truth"
    )


    plt.axis(
        "off"
    )


    # --------------------------------------
    # 3. PREDICTION
    # --------------------------------------

    plt.subplot(
        1, 4, 3
    )


    plt.imshow(
        prediction_display
    )


    plt.title(
        "Prediction"
    )


    plt.axis(
        "off"
    )


    # --------------------------------------
    # 4. OVERLAY
    # --------------------------------------

    plt.subplot(
        1, 4, 4
    )


    plt.imshow(
        original_image
    )


    plt.imshow(
        prediction_display,
        alpha=0.45
    )


    plt.title(
        "Prediction Overlay"
    )


    plt.axis(
        "off"
    )


    plt.tight_layout()


    # ======================================
    # SAVE VISUALIZATION
    # ======================================

    visualization_path = (
        output_dir
        / f"{image_name}_prediction_visualization.png"
    )


    plt.savefig(
        visualization_path,
        dpi=150,
        bbox_inches="tight"
    )


    plt.close()


    print(
        "\nVisualization saved:"
    )

    print(
        visualization_path
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 60)
print("20-IMAGE PREDICTION SUMMARY")
print("=" * 60)


if len(all_pixel_accuracies) > 0:

    average_pixel_accuracy = np.mean(
        all_pixel_accuracies
    )

else:

    average_pixel_accuracy = 0.0


if len(all_foreground_mious) > 0:

    average_foreground_miou = np.mean(
        all_foreground_mious
    )

else:

    average_foreground_miou = 0.0


print(
    f"Images successfully processed: "
    f"{len(all_pixel_accuracies)}"
)


print(
    f"Average Pixel Accuracy: "
    f"{average_pixel_accuracy:.4f}"
)


print(
    f"Average Foreground mIoU: "
    f"{average_foreground_miou:.4f}"
)


print(
    "\nAverage Per-Class IoU:"
)


for class_id in range(
    NUM_CLASSES
):

    if len(
        all_class_ious[class_id]
    ) > 0:

        average_iou = np.mean(
            all_class_ious[class_id]
        )

        print(
            f"Class {class_id:2d} "
            f"({CLASS_NAMES[class_id]:22s}) : "
            f"{average_iou:.4f}"
        )

    else:

        print(
            f"Class {class_id:2d} "
            f"({CLASS_NAMES[class_id]:22s}) : "
            f"N/A"
        )


print("\n")
print("=" * 60)
print("20-IMAGE PREDICTION COMPLETED")
print("=" * 60)