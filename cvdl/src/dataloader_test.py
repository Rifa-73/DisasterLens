import torch
from torch.utils.data import DataLoader

from dataset import FloodNetDataset


# Create dataset
dataset = FloodNetDataset(
    image_dir="/Users/rifa/Downloads/FloodNet-Supervised_v1/train/train-org-img",
    mask_dir="/Users/rifa/Downloads/FloodNet-Supervised_v1/train/train-label-img"
)

print("Dataset size:", len(dataset))


# Create DataLoader
loader = DataLoader(
    dataset,
    batch_size=4,
    shuffle=True,
    num_workers=0
)


# Get one batch
images, masks = next(iter(loader))

print("Images batch shape:", images.shape)
print("Masks batch shape:", masks.shape)
print("Images dtype:", images.dtype)
print("Masks dtype:", masks.dtype)