import sys
import json
from pathlib import Path
from collections import deque

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
CVDL_OUTPUTS = CVDL_ROOT / "outputs"

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

MODEL_PATH = CVDL_OUTPUTS / "best_model_weighted.pth"

INPUT_VIDEO = CVDL_OUTPUTS / "test_flood_video.mp4"

OUTPUT_VIDEO = CVDL_OUTPUTS / "test_flood_video_smoothed.mp4"

IMAGE_SIZE = (512, 512)

NUM_CLASSES = 10

# Number of previous frames used for smoothing
SMOOTHING_WINDOW = 3


# ============================================================
# FLOOD CLASSES
# ============================================================

FLOOD_CLASSES = {
    1,
    3,
    5
}


# ============================================================
# FLOOD LOGIT BIAS
# ============================================================

FLOOD_LOGIT_BIAS = {
    1: 0.10,
    3: 0.18,
    5: 0.05
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
# PREDICT FRAME
# ============================================================

def predict_frame(model, frame):

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    resized = cv2.resize(
        rgb_frame,
        IMAGE_SIZE
    )

    image_array = (
        resized.astype(np.float32)
        / 255.0
    )

    tensor = torch.from_numpy(
        image_array
    ).permute(
        2, 0, 1
    ).unsqueeze(0)

    tensor = tensor.to(DEVICE)

    with torch.no_grad():

        outputs = model(tensor)

        adjusted_outputs = outputs.clone()

        for class_id, bias in FLOOD_LOGIT_BIAS.items():

            adjusted_outputs[
                :, class_id, :, :
            ] += bias

        mask = torch.argmax(
            adjusted_outputs,
            dim=1
        )

    return (
        mask
        .squeeze(0)
        .cpu()
        .numpy()
    )


# ============================================================
# FLOOD COVERAGE
# ============================================================

def calculate_flood_coverage(mask):

    total_pixels = mask.size

    flood_pixels = np.isin(
        mask,
        list(FLOOD_CLASSES)
    ).sum()

    coverage = (
        flood_pixels
        / total_pixels
        * 100
    )

    return round(
        min(float(coverage), 100.0),
        2
    )


# ============================================================
# SEVERITY
# ============================================================

def get_severity(flood_coverage):

    if flood_coverage >= 30:
        return "High"

    elif flood_coverage >= 10:
        return "Medium"

    elif flood_coverage > 0:
        return "Low"

    return "None"


# ============================================================
# PROCESS VIDEO
# ============================================================

def process_video():

    print("\n" + "=" * 70)
    print("DISASTERLENS - TEMPORAL SMOOTHING")
    print("=" * 70)

    model = load_model()

    cap = cv2.VideoCapture(
        str(INPUT_VIDEO)
    )

    if not cap.isOpened():

        print(
            f"\nERROR: Cannot open video:\n{INPUT_VIDEO}"
        )

        return


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


    # --------------------------------------------------------
    # VIDEO WRITER
    # --------------------------------------------------------

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        str(OUTPUT_VIDEO),
        fourcc,
        fps,
        (width, height)
    )


    # --------------------------------------------------------
    # SMOOTHING BUFFER
    # --------------------------------------------------------

    history = deque(
        maxlen=SMOOTHING_WINDOW
    )


    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    raw_values = []

    smoothed_values = []

    high_frames = 0
    medium_frames = 0
    low_frames = 0

    frame_number = 0


    print("\nVideo Information")
    print("-" * 40)

    print(f"FPS: {fps}")
    print(
        f"Resolution: {width} x {height}"
    )
    print(
        f"Total Frames: {total_frames}"
    )
    print(
        f"Smoothing Window: "
        f"{SMOOTHING_WINDOW}"
    )

    print("\nProcessing video...\n")


    # ========================================================
    # FRAME LOOP
    # ========================================================

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_number += 1


        # ----------------------------------------------------
        # RAW PREDICTION
        # ----------------------------------------------------

        mask = predict_frame(
            model,
            frame
        )

        raw_flood = calculate_flood_coverage(
            mask
        )


        # ----------------------------------------------------
        # ADD TO HISTORY
        # ----------------------------------------------------

        history.append(
            raw_flood
        )


        # ----------------------------------------------------
        # TEMPORAL SMOOTHING
        # ----------------------------------------------------

        smoothed_flood = round(
            float(
                np.mean(history)
            ),
            2
        )


        severity = get_severity(
            smoothed_flood
        )


        # ----------------------------------------------------
        # STORE RESULTS
        # ----------------------------------------------------

        raw_values.append(
            raw_flood
        )

        smoothed_values.append(
            smoothed_flood
        )


        # ----------------------------------------------------
        # SEVERITY COUNT
        # ----------------------------------------------------

        if severity == "High":

            high_frames += 1

        elif severity == "Medium":

            medium_frames += 1

        elif severity == "Low":

            low_frames += 1


        # ----------------------------------------------------
        # DISPLAY ON FRAME
        # ----------------------------------------------------

        display_frame = frame.copy()


        cv2.rectangle(
            display_frame,
            (0, 0),
            (width, 95),
            (0, 0, 0),
            -1
        )


        cv2.putText(
            display_frame,
            f"Raw Flood: {raw_flood:.2f}%",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        cv2.putText(
            display_frame,
            f"Smoothed Flood: {smoothed_flood:.2f}%",
            (20, 58),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        cv2.putText(
            display_frame,
            f"Severity: {severity}",
            (20, 86),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        # ----------------------------------------------------
        # WRITE FRAME
        # ----------------------------------------------------

        writer.write(
            display_frame
        )


        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        if (
            frame_number == 1
            or frame_number == total_frames
        ):

            print(
                f"Frame {frame_number}/{total_frames} | "
                f"Raw: {raw_flood:.2f}% | "
                f"Smoothed: {smoothed_flood:.2f}% | "
                f"Severity: {severity}"
            )


    # ========================================================
    # RELEASE
    # ========================================================

    cap.release()
    writer.release()


    # ========================================================
    # FINAL STATISTICS
    # ========================================================

    if smoothed_values:

        average_smoothed = round(
            float(
                np.mean(
                    smoothed_values
                )
            ),
            2
        )

        peak_smoothed = round(
            float(
                np.max(
                    smoothed_values
                )
            ),
            2
        )

        peak_frame = (
            int(
                np.argmax(
                    smoothed_values
                )
            )
            + 1
        )

    else:

        average_smoothed = 0.0
        peak_smoothed = 0.0
        peak_frame = 0


    peak_severity = get_severity(
        peak_smoothed
    )


    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "frames_analyzed":
            frame_number,

        "smoothing_window":
            SMOOTHING_WINDOW,

        "average_raw_flood_coverage_pct":
            round(
                float(
                    np.mean(raw_values)
                ),
                2
            )
            if raw_values
            else 0.0,

        "average_smoothed_flood_coverage_pct":
            average_smoothed,

        "peak_smoothed_flood_coverage_pct":
            peak_smoothed,

        "peak_frame":
            peak_frame,

        "peak_severity":
            peak_severity,

        "high_frames":
            high_frames,

        "medium_frames":
            medium_frames,

        "low_frames":
            low_frames,

        "output_video":
            str(OUTPUT_VIDEO)
    }


    # ========================================================
    # SAVE JSON
    # ========================================================

    result_path = (
        CVDL_OUTPUTS
        / "video_smoothed_results.json"
    )

    with open(
        result_path,
        "w"
    ) as f:

        json.dump(
            result,
            f,
            indent=4
        )


    # ========================================================
    # PRINT
    # ========================================================

    print("\n" + "=" * 70)
    print("TEMPORAL SMOOTHING COMPLETE")
    print("=" * 70)

    print(
        f"\nAverage Raw Flood: "
        f"{result['average_raw_flood_coverage_pct']:.2f}%"
    )

    print(
        f"Average Smoothed Flood: "
        f"{result['average_smoothed_flood_coverage_pct']:.2f}%"
    )

    print(
        f"Peak Smoothed Flood: "
        f"{result['peak_smoothed_flood_coverage_pct']:.2f}%"
    )

    print(
        f"Peak Frame: "
        f"{result['peak_frame']}"
    )

    print(
        f"Peak Severity: "
        f"{result['peak_severity']}"
    )

    print(
        f"High Frames: "
        f"{result['high_frames']}"
    )

    print(
        f"Medium Frames: "
        f"{result['medium_frames']}"
    )

    print(
        f"Low Frames: "
        f"{result['low_frames']}"
    )

    print(
        f"\nOutput Video:\n"
        f"{OUTPUT_VIDEO}"
    )

    print(
        f"\nResult JSON:\n"
        f"{result_path}"
    )

    print("\n" + "=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    process_video()