import importlib
import sys
from pathlib import Path

import numpy as np
import pytest


def test_dense_alignment_preserves_feature_dot_products():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark/baselines"))
    try:
        align = importlib.import_module("validate_image_model_pairs").aligned_dense_kernel
        chw = np.arange(12).reshape(2, 2, 3)
        weight = np.array(
            [[1, -2, 3, -4, 5, -6, 7, -8, 9, -10, 11, -12], [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]]
        )
        kernel = align(weight, 2, 2, 3)
        np.testing.assert_array_equal(
            weight @ chw.flatten(), chw.transpose(1, 2, 0).flatten() @ kernel
        )
        assert not np.array_equal(
            weight @ chw.flatten(), chw.transpose(1, 2, 0).flatten() @ weight.T
        )
        with pytest.raises(ValueError):
            align(weight, 2, 2, 4)
    finally:
        sys.path.pop(0)
