from dataset import FloodNetDataset


IMAGE_DIR = "/Users/rifa/Downloads/FloodNet-Supervised_v1/train/train-org-img"
MASK_DIR = "/Users/rifa/Downloads/FloodNet-Supervised_v1/train/train-label-img"


dataset = FloodNetDataset(
    image_dir=IMAGE_DIR,
    mask_dir=MASK_DIR
)


print("Number of images:", len(dataset))


image, mask = dataset[0]


print("Image shape:", image.shape)
print("Mask shape:", mask.shape)
print("Mask dtype:", mask.dtype)
print("Mask classes:", mask.unique().tolist())