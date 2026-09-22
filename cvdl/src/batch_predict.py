import json
import sys
from pathlib import Path

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

MODEL_PATH = REPO_ROOT / "cvdl" / "outputs" / "best_model_weighted.pth"

IMAGE_FOLDER = (
    Path.home()
    / "Downloads"
    / "FloodNet-Supervised_v1"
    / "test"
    / "test-org-img"
)

OUTPUT_FOLDER = REPO_ROOT / "cvdl" / "outputs"

RESULTS_FILE = OUTPUT_FOLDER / "batch_results.json"
SUMMARY_FILE = OUTPUT_FOLDER / "batch_summary.json"


# ============================================================
# FLOOD CLASSES
# ============================================================

FLOOD_RELATED_CLASSES = [
    "Building-Flooded",
    "Road-Flooded",
    "Water"
]


# ============================================================
# IMAGE EXTENSIONS
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


# ============================================================
# PREDICT MULTIPLE IMAGES
# ============================================================

def predict_multiple_images(image_folder):

    print("\n" + "=" * 75)
    print("        DISASTERLENS - BATCH FLOOD ANALYSIS")
    print("=" * 75)

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
    # Find images
    # --------------------------------------------------------

    image_folder = Path(image_folder)

    if not image_folder.exists():

        print(
            f"\nERROR: Image folder does not exist:\n"
            f"{image_folder}"
        )

        return []

    image_files = sorted(
        [
            file
            for file in image_folder.iterdir()
            if file.is_file()
            and file.suffix.lower() in IMAGE_EXTENSIONS
        ]
    )

    if not image_files:

        print("\nNo images found.")

        return []

    print(
        f"\nFound {len(image_files)} images."
    )

    print(
        f"Input folder: {image_folder}"
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    results = []

    # --------------------------------------------------------
    # Process every image
    # --------------------------------------------------------

    for index, image_path in enumerate(
        image_files,
        start=1
    ):

        print(
            f"\n[{index}/{len(image_files)}] "
            f"{image_path.name}"
        )

        try:

            # ----------------------------------------------
            # Read image
            # ----------------------------------------------

            with open(
                image_path,
                "rb"
            ) as f:

                image_bytes = f.read()

            # ----------------------------------------------
            # Model prediction
            # ----------------------------------------------

            result = predictor.predict(
                image_bytes
            )

            # ----------------------------------------------
            # Calculate flood coverage
            # ----------------------------------------------

            flood_coverage = sum(
                result[
                    "class_percentages"
                ].get(
                    class_name,
                    0.0
                )
                for class_name in FLOOD_RELATED_CLASSES
            )

            flood_coverage = round(
                min(
                    flood_coverage,
                    100.0
                ),
                2
            )

            # ----------------------------------------------
            # Create result object
            # ----------------------------------------------

            result_data = {

                "image": image_path.name,

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

            results.append(
                result_data
            )

            # ----------------------------------------------
            # Console output
            # ----------------------------------------------

            print(
                f"    Flood Coverage : "
                f"{flood_coverage:.2f}%"
            )

            print(
                f"    Severity Score : "
                f"{result_data['severity_score']:.2f}"
            )

            print(
                f"    Severity Level : "
                f"{result_data['severity_label']}"
            )

        except Exception as e:

            print(
                f"    ERROR: {e}"
            )

    # ========================================================
    # SORT RESULTS
    # ========================================================

    results.sort(
        key=lambda x: x[
            "severity_score"
        ],
        reverse=True
    )

    # ========================================================
    # SAVE COMPLETE RESULTS
    # ========================================================

    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=4
        )

    # ========================================================
    # CALCULATE SUMMARY
    # ========================================================

    severity_counts = {
        "High": 0,
        "Medium": 0,
        "Low": 0,
        "None": 0
    }

    for result in results:

        label = result[
            "severity_label"
        ]

        if label in severity_counts:

            severity_counts[label] += 1

    # --------------------------------------------------------
    # Average flood coverage
    # --------------------------------------------------------

    if results:

        average_flood_coverage = sum(
            result[
                "flood_coverage_pct"
            ]
            for result in results
        ) / len(results)

    else:

        average_flood_coverage = 0.0

    # --------------------------------------------------------
    # Highest severity
    # --------------------------------------------------------

    if results:

        highest_severity = results[0]

    else:

        highest_severity = None

    # --------------------------------------------------------
    # Top 10
    # --------------------------------------------------------

    top_10 = results[:10]

    # ========================================================
    # SUMMARY OBJECT
    # ========================================================

    summary = {

        "total_images":
            len(results),

        "average_flood_coverage_pct":
            round(
                average_flood_coverage,
                2
            ),

        "severity_counts":
            severity_counts,

        "highest_severity":
            highest_severity,

        "top_10": top_10
    }

    # ========================================================
    # SAVE SUMMARY
    # ========================================================

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            summary,
            f,
            indent=4
        )

    # ========================================================
    # PRINT FINAL RANKING
    # ========================================================

    print("\n\n")
    print("=" * 75)
    print("                 SEVERITY PRIORITY RANKING")
    print("=" * 75)

    for rank, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\n#{rank}  "
            f"{result['image']}"
        )

        print(
            f"     Flood Coverage : "
            f"{result['flood_coverage_pct']:.2f}%"
        )

        print(
            f"     Severity Score : "
            f"{result['severity_score']:.2f}"
        )

        print(
            f"     Severity Level : "
            f"{result['severity_label']}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n")
    print("=" * 75)
    print("                       SUMMARY")
    print("=" * 75)

    print(
        f"\nTotal Images        : "
        f"{len(results)}"
    )

    print(
        f"Average Flood       : "
        f"{average_flood_coverage:.2f}%"
    )

    print(
        f"\nHigh                : "
        f"{severity_counts['High']}"
    )

    print(
        f"Medium              : "
        f"{severity_counts['Medium']}"
    )

    print(
        f"Low                 : "
        f"{severity_counts['Low']}"
    )

    print(
        f"None                : "
        f"{severity_counts['None']}"
    )

    # ========================================================
    # TOP 10
    # ========================================================

    print("\n")
    print("=" * 75)
    print("                   TOP 10 SEVERE AREAS")
    print("=" * 75)

    for rank, result in enumerate(
        top_10,
        start=1
    ):

        print(
            f"{rank:2d}. "
            f"{result['image']:<15} "
            f"{result['flood_coverage_pct']:>6.2f}%  "
            f"{result['severity_label']}"
        )

    # ========================================================
    # FILE LOCATIONS
    # ========================================================

    print("\n")
    print("=" * 75)
    print("RESULT FILES")
    print("=" * 75)

    print(
        f"\nComplete results:"
        f"\n{RESULTS_FILE}"
    )

    print(
        f"\nSummary:"
        f"\n{SUMMARY_FILE}"
    )

    print("\n" + "=" * 75)

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    predict_multiple_images(
        IMAGE_FOLDER
    )