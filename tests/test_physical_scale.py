import numpy as np
import pytest
from PIL import Image, ImageDraw

from src.data.transforms import create_physical_scale_transform


def physical_cell(side, diameter):
    image = Image.new('RGB', (side, side), 'white')
    start = (side - diameter) // 2
    ImageDraw.Draw(image).rectangle((start, start, start + diameter - 1, start + diameter - 1), fill='black')
    return image


def cell_width(tensor):
    return int((tensor[0, tensor.shape[1] // 2] < 0).sum())


def test_same_physical_cell_has_same_final_size():
    source = create_physical_scale_transform('mll23', 252)(physical_cell(288, 115))
    target = create_physical_scale_transform('acevedo', 252)(physical_cell(363, 100))
    assert source.shape == target.shape == (3, 252, 252)
    assert abs(cell_width(source) - cell_width(target)) <= 1
    assert abs(cell_width(source) - 101) <= 1


def test_target_uses_native_central_field_without_padding():
    image = Image.new('RGB', (360, 363), 'white')
    ImageDraw.Draw(image).rectangle((0, 0, 39, 362), fill='black')
    tensor = create_physical_scale_transform('acevedo', 252)(image)
    assert np.isfinite(tensor.numpy()).all()
    assert (tensor[0] > 0).all()
    with pytest.raises(ValueError, match='smaller'):
        create_physical_scale_transform('acevedo', 252)(Image.new('RGB', (249, 363)))


def test_unknown_dataset_is_rejected():
    with pytest.raises(ValueError, match='Unsupported'):
        create_physical_scale_transform('unknown', 252)
