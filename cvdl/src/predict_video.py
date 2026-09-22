import sys
import json
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

IMAGE_SIZE = (512, 512)

NUM_CLASSES = 10


# ============================================================
# FLOOD CLASSES
# ============================================================

FLOOD_CLASSES = {
    1,  # Building-Flooded
    3,  # Road-Flooded
    5   # Water
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
# VIDEO PREDICTOR
# ============================================================

class FloodVideoPredictor:

    def __init__(self, model_path=None):

        self.model_path = (
            Path(model_path)
            if model_path
            else MODEL_PATH
        )

        self.device = DEVICE

        self.model = self._load_model()


    # ========================================================
    # LOAD MODEL
    # ========================================================

    def _load_model(self):

        print("\nLoading U-Net model...")

        model = FloodNetUNet(
            num_classes=NUM_CLASSES
        )

        checkpoint = torch.load(
            self.model_path,
            map_location=self.device,
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

        model.to(self.device)
        model.eval()

        print(
            f"Model loaded on: {self.device}"
        )

        return model


    # ========================================================
    # PREDICT ONE FRAME
    # ========================================================

    def _predict_frame(self, frame):

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

        tensor = tensor.to(
            self.device
        )

        with torch.no_grad():

            outputs = self.model(
                tensor
            )

            adjusted_outputs = (
                outputs.clone()
            )

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


    # ========================================================
    # FLOOD COVERAGE
    # ========================================================

    def _calculate_flood_coverage(
        self,
        mask
    ):

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


    # ========================================================
    # SEVERITY
    # ========================================================

    def _get_severity(
        self,
        flood_coverage
    ):

        if flood_coverage >= 30:
            return "High"

        elif flood_coverage >= 10:
            return "Medium"

        elif flood_coverage > 0:
            return "Low"

        return "None"


    # ========================================================
    # PREDICT VIDEO
    # ========================================================

    def predict_video(
        self,
        video_path,
        output_path=None
    ):

        video_path = Path(video_path)

        if not video_path.exists():

            raise FileNotFoundError(
                f"Video not found: {video_path}"
            )


        # ----------------------------------------------------
        # OUTPUT PATH
        # ----------------------------------------------------

        if output_path is None:

            output_path = (
                CVDL_OUTPUTS
                / f"{video_path.stem}_segmented.mp4"
            )

        else:

            output_path = Path(
                output_path
            )


        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        # ----------------------------------------------------
        # OPEN VIDEO
        # ----------------------------------------------------

        cap = cv2.VideoCapture(
            str(video_path)
        )

        if not cap.isOpened():

            raise RuntimeError(
                "Could not open video."
            )


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


        # ----------------------------------------------------
        # OUTPUT VIDEO
        # ----------------------------------------------------

        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            fps,
            (width, height)
        )

        if not writer.isOpened():

            cap.release()

            raise RuntimeError(
                "Could not create output video."
            )


        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        flood_values = []

        high_frames = 0
        medium_frames = 0
        low_frames = 0

        frame_number = 0

        peak_frame = 0
        peak_flood = 0.0


        # ----------------------------------------------------
        # PROCESS FRAMES
        # ----------------------------------------------------

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            frame_number += 1


            # Prediction
            mask = self._predict_frame(
                frame
            )


            # Flood %
            flood_coverage = (
                self._calculate_flood_coverage(
                    mask
                )
            )


            # Severity
            severity = self._get_severity(
                flood_coverage
            )


            # Store statistics
            flood_values.append(
                flood_coverage
            )


            if severity == "High":

                high_frames += 1

            elif severity == "Medium":

                medium_frames += 1

            elif severity == "Low":

                low_frames += 1


            # Peak
            if flood_coverage > peak_flood:

                peak_flood = flood_coverage

                peak_frame = frame_number


            # Write original frame
            writer.write(frame)


        # ----------------------------------------------------
        # RELEASE
        # ----------------------------------------------------

        cap.release()
        writer.release()


        # ----------------------------------------------------
        # FINAL STATISTICS
        # ----------------------------------------------------

        if flood_values:

            average_flood = round(
                float(
                    np.mean(flood_values)
                ),
                2
            )

        else:

            average_flood = 0.0


        peak_severity = self._get_severity(
            peak_flood
        )


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        result = {

            "video": video_path.name,

            "frames_analyzed":
                frame_number,

            "fps":
                fps,

            "average_flood_coverage_pct":
                average_flood,

            "peak_flood_coverage_pct":
                peak_flood,

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
                str(output_path)
        }


        return result


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print(
        "DISASTERLENS - VIDEO PREDICTION API"
    )
    print("=" * 70)


    input_video = (
        CVDL_OUTPUTS
        / "test_flood_video.mp4"
    )


    predictor = FloodVideoPredictor()


    result = predictor.predict_video(
        input_video
    )


    print("\n" + "=" * 70)
    print("VIDEO RESULT")
    print("=" * 70)


    print(
        json.dumps(
            result,
            indent=4
        )
    )


    print("\n" + "=" * 70)
    print(
        "VIDEO PREDICTION COMPLETE"
    )
    print("=" * 70)