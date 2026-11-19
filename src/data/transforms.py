"""Image transforms used by VecToMorph."""

from __future__ import annotations

from torchvision import transforms
from torchvision.transforms import functional as TF


IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


class PhysicalField:
    """Keep the central nominal 25um field, then sample it at 10px/um."""

    def __init__(self, dataset_name: str):
        native_sides = {'mll23': 288, 'acevedo': 250}
        if dataset_name not in native_sides:
            raise ValueError(f'Unsupported physical-scale dataset: {dataset_name}')
        self.native_side = native_sides[dataset_name]

    def __call__(self, image):
        if min(image.size) < self.native_side:
            raise ValueError('Image is smaller than the requested physical field; padding is forbidden.')
        image = TF.center_crop(image, [self.native_side, self.native_side])
        return TF.resize(image, [250, 250], interpolation=transforms.InterpolationMode.BICUBIC, antialias=True)


def create_physical_scale_transform(dataset_name: str, image_size: int = 252):
    """Normalize nominal physical field without estimating cell size or centre."""
    if image_size <= 0 or image_size % 14:
        raise ValueError('Image size must be a positive multiple of the 14px model patch size.')
    pixel_steps = [
        PhysicalField(dataset_name),
        transforms.Resize((image_size, image_size), interpolation=transforms.InterpolationMode.BICUBIC, antialias=True),
    ]
    return transforms.Compose(pixel_steps + [
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def create_embedding_transform(image_size: int = 224) -> transforms.Compose:
    """Create the deterministic transform used for embedding extraction."""
    return transforms.Compose(
        [
            transforms.Resize(
                image_size,
                interpolation=transforms.InterpolationMode.BICUBIC,
                antialias=True,
            ),
            transforms.CenterCrop((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )
