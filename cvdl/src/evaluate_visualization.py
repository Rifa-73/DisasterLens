import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# CVDL FINAL EVALUATION VISUALIZATION
# ============================================================

# Results obtained from full 450-image validation
classes = [
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

iou = [
    0.0000,
    0.5257,
    0.6080,
    0.3349,
    0.7279,
    0.5957,
    0.7583,
    0.4202,
    0.5270,
    0.8409
]

pixel_accuracy = 0.8521
foreground_miou = 0.5932
flooded_miou = 0.4303
non_flooded_miou = 0.6680


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

output_dir = "outputs"


# ============================================================
# 1. PER-CLASS IoU
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(classes, iou)

plt.ylabel("IoU")
plt.xlabel("Class")
plt.title("CVDL Per-Class IoU")

plt.xticks(
    rotation=45,
    ha="right"
)

plt.ylim(0, 1)

for i, value in enumerate(iou):
    plt.text(
        i,
        value + 0.02,
        f"{value:.3f}",
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    f"{output_dir}/cvdl_per_class_iou.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 2. FLOODED vs NON-FLOODED mIoU
# ============================================================

groups = [
    "Flooded\nClasses",
    "Non-Flooded\nClasses"
]

values = [
    flooded_miou,
    non_flooded_miou
]

plt.figure(figsize=(7, 6))

plt.bar(groups, values)

plt.ylabel("mIoU")
plt.title("CVDL Flooded vs Non-Flooded Performance")

plt.ylim(0, 1)

for i, value in enumerate(values):
    plt.text(
        i,
        value + 0.02,
        f"{value:.4f}",
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    f"{output_dir}/cvdl_flooded_vs_nonflooded.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 3. OVERALL METRICS
# ============================================================

metric_names = [
    "Pixel Accuracy",
    "Foreground mIoU",
    "Flooded mIoU",
    "Non-Flooded mIoU"
]

metric_values = [
    pixel_accuracy,
    foreground_miou,
    flooded_miou,
    non_flooded_miou
]

plt.figure(figsize=(9, 6))

plt.bar(
    metric_names,
    metric_values
)

plt.ylabel("Score")
plt.title("CVDL Overall Validation Metrics")

plt.ylim(0, 1)

plt.xticks(
    rotation=20,
    ha="right"
)

for i, value in enumerate(metric_values):
    plt.text(
        i,
        value + 0.02,
        f"{value:.4f}",
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    f"{output_dir}/cvdl_overall_metrics.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 4. SAVE NUMERICAL RESULTS
# ============================================================

with open(
    f"{output_dir}/cvdl_final_results.txt",
    "w"
) as f:

    f.write("CVDL FULL VALIDATION RESULTS\n")
    f.write("=" * 60 + "\n\n")

    f.write("Validation Images: 450\n")
    f.write(f"Pixel Accuracy: {pixel_accuracy:.4f}\n")
    f.write(f"Foreground mIoU: {foreground_miou:.4f}\n")
    f.write(f"Flooded Classes mIoU: {flooded_miou:.4f}\n")
    f.write(
        f"Non-Flooded Classes mIoU: "
        f"{non_flooded_miou:.4f}\n\n"
    )

    f.write("Per-Class IoU\n")
    f.write("-" * 60 + "\n")

    for name, value in zip(classes, iou):
        f.write(
            f"{name:<25} : {value:.4f}\n"
        )


# ============================================================
# COMPLETE
# ============================================================

print("=" * 60)
print("CVDL EVALUATION VISUALIZATION COMPLETE")
print("=" * 60)

print("\nGenerated files:")

print("1. outputs/cvdl_per_class_iou.png")
print("2. outputs/cvdl_flooded_vs_nonflooded.png")
print("3. outputs/cvdl_overall_metrics.png")
print("4. outputs/cvdl_final_results.txt")

print("\nAll CVDL results saved successfully.")