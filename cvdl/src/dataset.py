from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms


class FloodNetDataset(Dataset):

    def __init__(self, image_dir, mask_dir, image_size=(512, 512)):

        self.image_dir = Path(image_dir)
        self.mask_dir = Path(mask_dir)
        self.image_size = image_size

        self.images = sorted(self.image_dir.glob("*.jpg"))

        self.image_transform = transforms.Compose([
            transforms.Resize(image_size),
            transforms.ToTensor()
        ])

        self.mask_transform = transforms.Resize(
            image_size,
            interpolation=transforms.InterpolationMode.NEAREST
        )

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):

        image_path = self.images[index]

        image_name = image_path.stem
        mask_path = self.mask_dir / f"{image_name}_lab.png"

        image = Image.open(image_path).convert("RGB")
        mask = Image.open(mask_path).convert("L")

        image = self.image_transform(image)

        mask = self.mask_transform(mask)

        mask = np.array(mask, dtype=np.int64)
        mask = torch.from_numpy(mask)

        return image, mask