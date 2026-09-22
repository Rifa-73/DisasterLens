import json
import sys
from pathlib import Path

import cv2


# ============================================================
# PATH SETUP
# ============================================================

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CVDL_SRC = REPO_ROOT / "cvdl" / "src"

if str(CVDL_SRC) not in sys.path:
    sys.path.insert(0, str(CVDL_SRC))


# ============================================================
# IMPORT EXISTING PREDICTOR
# ============================================================

from predict_api import FloodPredictor


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = (
    REPO_ROOT
    / "cvdl"
    / "outputs"
    / "best_model_weighted.pth"
)

OUTPUT_FOLDER = REPO_ROOT / "cvdl" / "outputs"

RESULT_FILE = OUTPUT_FOLDER / "video_results.json"

# Process one frame every 2 seconds
FRAME_INTERVAL_SECONDS = 2.0


# ============================================================
# FLOOD CLASSES
# ============================================================

FLOOD_RELATED_CLASSES = [
    "Building-Flooded",
    "Road-Flooded",
    "Water"
]


# ============================================================
# VIDEO TIME FORMAT
# ============================================================

def format_timestamp(seconds):

    minutes = int(seconds // 60)

    remaining_seconds = int(
        seconds % 60
    )

    return (
        f"{minutes:02d}:"
        f"{remaining_seconds:02d}"
    )


# ============================================================
# VIDEO PREDICTION
# ============================================================

def predict_video(
    video_path,
    frame_interval=FRAME_INTERVAL_SECONDS
):

    print("\n" + "=" * 75)
    print("        DISASTERLENS - VIDEO FLOOD ANALYSIS")
    print("=" * 75)

    video_path = Path(video_path)

    # --------------------------------------------------------
    # Check video
    # --------------------------------------------------------

    if not video_path.exists():

        print(
            f"\nERROR: Video not found:\n"
            f"{video_path}"
        )

        return None

    # --------------------------------------------------------
    # Create output folder
    # --------------------------------------------------------

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print("\nLoading model...")

    predictor = FloodPredictor(
        str(MODEL_PATH)
    )

    print("Model loaded successfully.")

    # --------------------------------------------------------
    # Open video
    # --------------------------------------------------------

    cap = cv2.VideoCapture(
        str(video_path)
    )

    if not cap.isOpened():

        print(
            "\nERROR: Could not open video."
        )

        return None

    # --------------------------------------------------------
    # Video information
    # --------------------------------------------------------

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    duration = (
        total_frames / fps
        if fps > 0
        else 0
    )

    print("\nVideo information:")
    print(
        f"    FPS       : {fps:.2f}"
    )
    print(
        f"    Frames    : {total_frames}"
    )
    print(
        f"    Duration  : "
        f"{format_timestamp(duration)}"
    )
    print(
        f"    Sampling  : "
        f"Every {frame_interval} seconds"
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    frame_results = []

    next_sample_time = 0.0

    # --------------------------------------------------------
    # Process video
    # --------------------------------------------------------

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        # Current frame time
        current_time = (
            cap.get(
                cv2.CAP_PROP_POS_MSEC
            ) / 1000.0
        )

        # ----------------------------------------------------
        # Sample frame
        # ----------------------------------------------------

        if current_time >= next_sample_time:

            timestamp = format_timestamp(
                current_time
            )

            print(
                f"\nProcessing frame "
                f"at {timestamp}"
            )

            try:

                # --------------------------------------------
                # Convert frame to JPEG bytes
                # --------------------------------------------

                success, encoded_frame = cv2.imencode(
                    ".jpg",
                    frame
                )

                if not success:

                    print(
                        "    Could not encode frame."
                    )

                    next_sample_time += (
                        frame_interval
                    )

                    continue

                image_bytes = (
                    encoded_frame.tobytes()
                )

                # --------------------------------------------
                # Prediction
                # --------------------------------------------

                result = predictor.predict(
                    image_bytes
                )

                # --------------------------------------------
                # Flood coverage
                # --------------------------------------------

                flood_coverage = sum(
                    result[
                        "class_percentages"
                    ].get(
                        class_name,
                        0.0
                    )
                    for class_name
                    in FLOOD_RELATED_CLASSES
                )

                flood_coverage = round(
                    min(
                        flood_coverage,
                        100.0
                    ),
                    2
                )

                # --------------------------------------------
                # Store frame result
                # --------------------------------------------

                frame_result = {

                    "timestamp_seconds":
                        round(
                            current_time,
                            2
                        ),

                    "timestamp":
                        timestamp,

                    "flood_coverage_pct":
                        flood_coverage,

                    "severity_score":
                        float(
                            result[
                                "severity_score"
                            ]
                        ),

                    "severity_label":
                        result[
                            "severity_label"
                        ],

                    "class_percentages":
                        {
                            key: round(
                                float(value),
                                2
                            )
                            for key, value
                            in result[
                                "class_percentages"
                            ].items()
                        }
                }

                frame_results.append(
                    frame_result
                )

                # --------------------------------------------
                # Console output
                # --------------------------------------------

                print(
                    f"    Flood Coverage : "
                    f"{flood_coverage:.2f}%"
                )

                print(
                    f"    Severity Score : "
                    f"{frame_result['severity_score']:.2f}"
                )

                print(
                    f"    Severity Level : "
                    f"{frame_result['severity_label']}"
                )

            except Exception as e:

                print(
                    f"    ERROR: {e}"
                )

            next_sample_time += (
                frame_interval
            )

    # --------------------------------------------------------
    # Release video
    # --------------------------------------------------------

    cap.release()

    # ========================================================
    # NO RESULTS
    # ========================================================

    if not frame_results:

        print(
            "\nNo frames were successfully processed."
        )

        return None

    # ========================================================
    # CALCULATE VIDEO STATISTICS
    # ========================================================

    flood_coverages = [
        result[
            "flood_coverage_pct"
        ]
        for result in frame_results
    ]

    severity_scores = [
        result[
            "severity_score"
        ]
        for result in frame_results
    ]

    # --------------------------------------------------------
    # Average
    # --------------------------------------------------------

    average_flood_coverage = (
        sum(flood_coverages)
        / len(flood_coverages)
    )

    average_severity_score = (
        sum(severity_scores)
        / len(severity_scores)
    )

    # --------------------------------------------------------
    # Peak
    # --------------------------------------------------------

    peak_result = max(
        frame_results,
        key=lambda x: x[
            "severity_score"
        ]
    )

    # ========================================================
    # SEVERITY COUNTS
    # ========================================================

    severity_counts = {
        "High": 0,
        "Medium": 0,
        "Low": 0,
        "None": 0
    }

    for result in frame_results:

        label = result[
            "severity_label"
        ]

        if label in severity_counts:

            severity_counts[label] += 1

    # ========================================================
    # FINAL VIDEO RESULT
    # ========================================================

    video_result = {

        "video": str(video_path),

        "duration_seconds":
            round(
                duration,
                2
            ),

        "duration":
            format_timestamp(
                duration
            ),

        "sampling_interval_seconds":
            frame_interval,

        "frames_analyzed":
            len(frame_results),

        "average_flood_coverage_pct":
            round(
                average_flood_coverage,
                2
            ),

        "average_severity_score":
            round(
                average_severity_score,
                2
            ),

        "peak_flood_coverage_pct":
            peak_result[
                "flood_coverage_pct"
            ],

        "peak_severity_score":
            peak_result[
                "severity_score"
            ],

        "peak_severity_label":
            peak_result[
                "severity_label"
            ],

        "peak_timestamp":
            peak_result[
                "timestamp"
            ],

        "severity_counts":
            severity_counts,

        "frame_results":
            frame_results
    }

    # ========================================================
    # SAVE JSON
    # ========================================================

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            video_result,
            f,
            indent=4
        )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print("\n")
    print("=" * 75)
    print("                  VIDEO ANALYSIS SUMMARY")
    print("=" * 75)

    print(
        f"\nVideo               : "
        f"{video_path.name}"
    )

    print(
        f"Duration            : "
        f"{format_timestamp(duration)}"
    )

    print(
        f"Frames analyzed     : "
        f"{len(frame_results)}"
    )

    print(
        f"\nAverage Flood       : "
        f"{average_flood_coverage:.2f}%"
    )

    print(
        f"Average Severity    : "
        f"{average_severity_score:.2f}"
    )

    print(
        f"\nPeak Flood          : "
        f"{peak_result['flood_coverage_pct']:.2f}%"
    )

    print(
        f"Peak Severity       : "
        f"{peak_result['severity_score']:.2f}"
    )

    print(
        f"Peak Severity Level : "
        f"{peak_result['severity_label']}"
    )

    print(
        f"Peak Timestamp      : "
        f"{peak_result['timestamp']}"
    )

    print("\nSeverity Distribution:")

    print(
        f"    High   : "
        f"{severity_counts['High']}"
    )

    print(
        f"    Medium : "
        f"{severity_counts['Medium']}"
    )

    print(
        f"    Low    : "
        f"{severity_counts['Low']}"
    )

    print(
        f"    None   : "
        f"{severity_counts['None']}"
    )

    print("\n")
    print("=" * 75)
    print("RESULT FILE")
    print("=" * 75)

    print(
        f"\n{RESULT_FILE}"
    )

    print("\n" + "=" * 75)

    return video_result


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "\nUsage:"
        )

        print(
            "\nPYTHONPATH=. python "
            "cvdl/src/video_predict.py "
            "/path/to/video.mp4"
        )

        print(
            "\nExample:"
        )

        print(
            "PYTHONPATH=. python "
            "cvdl/src/video_predict.py "
            "~/Downloads/flood_video.mp4"
        )

        sys.exit(1)

    video_path = sys.argv[1]

    predict_video(
        video_path
    )