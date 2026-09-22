import json
from pathlib import Path

import cv2


# ============================================================
# PATHS
# ============================================================

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

RESULTS_FILE = (
    REPO_ROOT
    / "cvdl"
    / "outputs"
    / "batch_results.json"
)

IMAGE_FOLDER = (
    Path.home()
    / "Downloads"
    / "FloodNet-Supervised_v1"
    / "test"
    / "test-org-img"
)

OUTPUT_VIDEO = (
    REPO_ROOT
    / "cvdl"
    / "outputs"
    / "test_flood_video.mp4"
)


# ============================================================
# SETTINGS
# ============================================================

FPS = 1
NUMBER_OF_IMAGES = 10

FRAME_WIDTH = 640
FRAME_HEIGHT = 512


# ============================================================
# CHECK FILES
# ============================================================

if not RESULTS_FILE.exists():
    print("ERROR: batch_results.json not found:")
    print(RESULTS_FILE)
    raise SystemExit(1)

if not IMAGE_FOLDER.exists():
    print("ERROR: FloodNet image folder not found:")
    print(IMAGE_FOLDER)
    raise SystemExit(1)


# ============================================================
# LOAD BATCH RESULTS
# ============================================================

with open(
    RESULTS_FILE,
    "r",
    encoding="utf-8"
) as f:
    results = json.load(f)


if not results:
    print("ERROR: No results found in batch_results.json")
    raise SystemExit(1)


# ============================================================
# SELECT TOP SEVERE IMAGES
# ============================================================

top_images = results[:NUMBER_OF_IMAGES]

print("\n" + "=" * 65)
print("SELECTED IMAGES FOR TEST VIDEO")
print("=" * 65)

for index, result in enumerate(
    top_images,
    start=1
):
    print(
        f"{index:2d}. "
        f"{result['image']:<15} "
        f"{result['flood_coverage_pct']:>6.2f}%  "
        f"{result['severity_label']}"
    )


# ============================================================
# CREATE VIDEO WRITER
# ============================================================

OUTPUT_VIDEO.parent.mkdir(
    parents=True,
    exist_ok=True
)

fourcc = cv2.VideoWriter_fourcc(
    *"mp4v"
)

writer = cv2.VideoWriter(
    str(OUTPUT_VIDEO),
    fourcc,
    FPS,
    (
        FRAME_WIDTH,
        FRAME_HEIGHT
    )
)


if not writer.isOpened():
    print("\nERROR: Could not create video writer.")
    raise SystemExit(1)


# ============================================================
# ADD IMAGES TO VIDEO
# ============================================================

written_frames = 0

for result in top_images:

    image_path = (
        IMAGE_FOLDER
        / result["image"]
    )

    print(
        f"\nAdding: {result['image']}"
    )

    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        print(
            f"WARNING: Could not read {image_path}"
        )
        continue

    # Resize image
    image = cv2.resize(
        image,
        (
            FRAME_WIDTH,
            FRAME_HEIGHT
        )
    )

    writer.write(image)

    written_frames += 1


# ============================================================
# RELEASE
# ============================================================

writer.release()


# ============================================================
# FINAL CHECK
# ============================================================

if written_frames == 0:

    print("\nERROR: No frames were written.")
    raise SystemExit(1)


if not OUTPUT_VIDEO.exists():

    print(
        "\nERROR: Video file was not created."
    )

    raise SystemExit(1)


print("\n" + "=" * 65)
print("              TEST VIDEO CREATED")
print("=" * 65)

print(
    f"\nFrames written : {written_frames}"
)

print(
    f"Video saved at:\n"
    f"{OUTPUT_VIDEO}"
)

print(
    f"\nVideo size: "
    f"{OUTPUT_VIDEO.stat().st_size / (1024 * 1024):.2f} MB"
)

print("\nOpen it using:")

print(
    f'open "{OUTPUT_VIDEO}"'
)

print("\n" + "=" * 65)
