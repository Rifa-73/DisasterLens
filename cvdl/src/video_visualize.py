import sys
from pathlib import Path

import cv2
import numpy as np
import torch


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

INPUT_VIDEO = CVDL_ROOT / "outputs" / "test_flood_video.mp4"

OUTPUT_VIDEO = CVDL_ROOT / "outputs" / "test_flood_video_segmented.mp4"

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
# COLORS
# RGB FORMAT
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
# DEVICE
# ============================================================

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")


# ============================================================
# FLOOD LOGIT BIAS
# Same logic used in predict_api.py
# ============================================================

FLOOD_LOGIT_BIAS = {
    1: 0.10,
    3: 0.18,
    5: 0.05
}


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    print("\nLoading U-Net model...")

    model = FloodNetUNet(num_classes=NUM_CLASSES)

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
        weights_only=False
    )

    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.to(DEVICE)
    model.eval()

    print(f"Model loaded on: {DEVICE}")

    return model


# ============================================================
# PREDICT FRAME
# ============================================================

def predict_frame(model, frame):

    # OpenCV BGR → RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Resize
    resized = cv2.resize(
        rgb_frame,
        IMAGE_SIZE
    )

    # Normalize
    image_array = resized.astype(np.float32) / 255.0

    # HWC → CHW
    tensor = torch.from_numpy(
        image_array
    ).permute(2, 0, 1).unsqueeze(0)

    tensor = tensor.to(DEVICE)

    # Model prediction
    with torch.no_grad():

        outputs = model(tensor)

        adjusted_outputs = outputs.clone()

        for class_id, bias in FLOOD_LOGIT_BIAS.items():
            adjusted_outputs[:, class_id, :, :] += bias

        mask = torch.argmax(
            adjusted_outputs,
            dim=1
        )

    return mask.squeeze(0).cpu().numpy()


# ============================================================
# CREATE COLOR MASK
# ============================================================

def create_color_mask(mask):

    h, w = mask.shape

    color_mask = np.zeros(
        (h, w, 3),
        dtype=np.uint8
    )

    for class_id, color in CLASS_COLORS.items():

        color_mask[mask == class_id] = color

    return color_mask


# ============================================================
# CALCULATE FLOOD COVERAGE
# ============================================================

def calculate_flood_coverage(mask):

    total_pixels = mask.size

    flood_pixels = np.isin(
        mask,
        list(FLOOD_CLASSES)
    ).sum()

    flood_percentage = (
        flood_pixels / total_pixels
    ) * 100

    return min(
        float(flood_percentage),
        100.0
    )


# ============================================================
# SEVERITY
# ============================================================

def get_severity(flood_coverage):

    if flood_coverage >= 30:
        return "HIGH"

    elif flood_coverage >= 10:
        return "MEDIUM"

    elif flood_coverage > 0:
        return "LOW"

    else:
        return "NONE"


# ============================================================
# CREATE FRAME OVERLAY
# ============================================================

def create_overlay(frame, mask):

    # Resize segmentation mask to original frame size
    height, width = frame.shape[:2]

    mask_resized = cv2.resize(
        mask.astype(np.uint8),
        (width, height),
        interpolation=cv2.INTER_NEAREST
    )

    # RGB color mask
    color_mask_rgb = create_color_mask(
        mask_resized
    )

    # RGB → BGR for OpenCV
    color_mask_bgr = cv2.cvtColor(
        color_mask_rgb,
        cv2.COLOR_RGB2BGR
    )

    # Overlay
    overlay = cv2.addWeighted(
        frame,
        0.60,
        color_mask_bgr,
        0.40,
        0
    )

    return overlay


# ============================================================
# ADD INFORMATION PANEL
# ============================================================

def add_information(
    frame,
    flood_coverage,
    severity,
    frame_number,
    total_frames
):

    output = frame.copy()

    # Top information panel
    panel_height = 105

    panel = np.zeros(
        (
            panel_height,
            output.shape[1],
            3
        ),
        dtype=np.uint8
    )

    output = np.vstack(
        [panel, output]
    )

    # Flood coverage
    cv2.putText(
        output,
        f"Flood Coverage: {flood_coverage:.2f}%",
        (20, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    # Severity
    cv2.putText(
        output,
        f"Severity: {severity}",
        (20, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    # Frame number
    cv2.putText(
        output,
        f"Frame: {frame_number}/{total_frames}",
        (output.shape[1] - 250, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.60,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    return output


# ============================================================
# PROCESS VIDEO
# ============================================================

def process_video():

    print("\n" + "=" * 70)
    print("       DISASTERLENS - VIDEO SEGMENTATION")
    print("=" * 70)

    # Check input
    if not INPUT_VIDEO.exists():

        print("\nERROR: Input video not found:")
        print(INPUT_VIDEO)

        return

    # Load model
    model = load_model()

    # Open video
    cap = cv2.VideoCapture(
        str(INPUT_VIDEO)
    )

    if not cap.isOpened():

        print("\nERROR: Could not open video.")

        return

    # Video properties
    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    width = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    height = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    print("\nVideo Information")
    print("-" * 40)
    print(f"FPS: {fps}")
    print(f"Resolution: {width} x {height}")
    print(f"Total Frames: {total_frames}")

    # Output size includes information panel
    output_width = width
    output_height = height + 105

    # Video writer
    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        str(OUTPUT_VIDEO),
        fourcc,
        fps,
        (
            output_width,
            output_height
        )
    )

    if not writer.isOpened():

        print("\nERROR: Could not create output video.")

        cap.release()

        return

    # Statistics
    flood_values = []

    high_frames = 0
    medium_frames = 0
    low_frames = 0

    frame_number = 0

    print("\nProcessing video...\n")

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_number += 1

        # Prediction
        mask = predict_frame(
            model,
            frame
        )

        # Flood coverage
        flood_coverage = calculate_flood_coverage(
            mask
        )

        # Severity
        severity = get_severity(
            flood_coverage
        )

        # Statistics
        flood_values.append(
            flood_coverage
        )

        if severity == "HIGH":
            high_frames += 1

        elif severity == "MEDIUM":
            medium_frames += 1

        elif severity == "LOW":
            low_frames += 1

        # Create segmentation overlay
        overlay = create_overlay(
            frame,
            mask
        )

        # Add information
        final_frame = add_information(
            overlay,
            flood_coverage,
            severity,
            frame_number,
            total_frames
        )

        # Write frame
        writer.write(
            final_frame
        )

        # Progress
        if frame_number % 10 == 0 or frame_number == 1:

            print(
                f"Frame {frame_number}/{total_frames} | "
                f"Flood: {flood_coverage:.2f}% | "
                f"Severity: {severity}"
            )

    # Release
    cap.release()
    writer.release()

    # ========================================================
    # FINAL STATISTICS
    # ========================================================

    if flood_values:

        average_flood = float(
            np.mean(flood_values)
        )

        peak_flood = float(
            np.max(flood_values)
        )

        peak_frame = int(
            np.argmax(flood_values) + 1
        )

    else:

        average_flood = 0.0
        peak_flood = 0.0
        peak_frame = 0

    peak_severity = get_severity(
        peak_flood
    )

    print("\n" + "=" * 70)
    print("VIDEO SEGMENTATION COMPLETE")
    print("=" * 70)

    print(f"\nFrames analyzed: {frame_number}")

    print(
        f"Average Flood Coverage: "
        f"{average_flood:.2f}%"
    )

    print(
        f"Peak Flood Coverage: "
        f"{peak_flood:.2f}%"
    )

    print(
        f"Peak Frame: "
        f"{peak_frame}"
    )

    print(
        f"Peak Severity: "
        f"{peak_severity}"
    )

    print(
        f"\nHigh Frames: {high_frames}"
    )

    print(
        f"Medium Frames: {medium_frames}"
    )

    print(
        f"Low Frames: {low_frames}"
    )

    print(
        f"\nOutput Video:\n{OUTPUT_VIDEO}"
    )

    print("\n" + "=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    process_video()