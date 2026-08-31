import numpy as np
from PIL import Image
from pathlib import Path
from collections import Counter


mask_dir = Path(
    "/Users/rifa/Downloads/FloodNet-Supervised_v1/train/train-label-img"
)


# FloodNet class names
class_names = {
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


counter = Counter()

mask_files = list(mask_dir.glob("*.png"))


# Read every mask
for mask_path in mask_files:

    mask = np.array(Image.open(mask_path))

    values, counts = np.unique(mask, return_counts=True)

    for value, count in zip(values, counts):
        counter[int(value)] += int(count)


print("\n========== FLOODNET CLASS DISTRIBUTION ==========\n")

print("Number of mask images:", len(mask_files))

print("\nClasses found:\n")

for class_id in sorted(counter.keys()):

    print(
        f"Class {class_id} - "
        f"{class_names[class_id]}: "
        f"{counter[class_id]:,} pixels"
    )


print("\nUnique class IDs:")
print(sorted(counter.keys()))

print("\nNumber of classes:")
print(len(counter))