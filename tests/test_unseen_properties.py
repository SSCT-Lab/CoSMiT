import importlib
import sys
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def oracle():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark/baselines"))
    yield importlib.import_module("unseen_properties")
    sys.path.pop(0)


def test_explicit_reference_examples(oracle):
    x = np.array([[1.0, 2.0], [3.0, 4.0]])
    cases = [
        ("matmul", [[7, 10], [15, 22]]),
        ("det", -2),
        ("trace", 5),
        ("prod", [3, 8]),
        ("cumsum", [[1, 2], [4, 6]]),
        ("cumprod", [[1, 2], [3, 8]]),
    ]
    for family, expected in cases:
        np.testing.assert_array_equal(oracle.reference(family, x, x, 0, False, np), expected)
    np.testing.assert_array_equal(oracle.reference("prod", x, None, -1, True, np), [[2], [12]])
    np.testing.assert_array_equal(
        oracle.reference("trace", np.array([[1, 2, 3], [4, 5, 6]]), None, 0, False, np), 6
    )


def test_domain_rejects_bad_geometry_and_unregistered_values(oracle):
    eye = np.eye(2, dtype="float32")
    assert oracle.valid_domain("det", eye, None, 0, np)
    assert not oracle.valid_domain("det", np.ones((2, 2)), None, 0, np)
    assert not oracle.valid_domain("det", np.ones((2, 3)), None, 0, np)
    assert not oracle.valid_domain("prod", eye, None, 2, np)
    assert not oracle.valid_domain("prod", eye.astype("int32"), None, 0, np)
    assert not oracle.valid_domain("matmul", eye, np.ones((3, 2)), 0, np)
    assert not oracle.valid_domain("trace", np.array([[np.nan]]), None, 0, np)
