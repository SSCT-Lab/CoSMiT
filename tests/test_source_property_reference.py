import importlib
import sys
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def reference():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark/baselines"))
    yield importlib.import_module("source_property_reference")
    sys.path.pop(0)


def test_domain_rejects_invalid_values_dtype_shape_and_size(reference):
    domain = {
        "closed_interval": [0, 8],
        "dtypes": ["float32", "float64"],
        "rank_max": 4,
        "elements_max": 4096,
    }
    assert reference.valid_input(np.array([0, 8], dtype="float32"), domain, np)
    for value in [
        np.array([-1.0]),
        np.array([float("nan")]),
        np.array([float("inf")]),
        np.array([1]),
        np.zeros((1, 1, 1, 1, 1)),
        np.zeros(4097),
    ]:
        assert not reference.valid_input(value, domain, np)


def test_domains_restrict_poles_and_invalid_real_values(reference):
    from collect_public_corpus import bounds

    for family, invalid in [
        ("log", 0),
        ("sqrt", -1),
        ("reciprocal", 0),
        ("acos", 1.01),
        ("log1p", -1),
    ]:
        domain = {
            "closed_interval": bounds(family),
            "dtypes": ["float64"],
            "rank_max": 4,
            "elements_max": 4096,
        }
        assert not reference.valid_input(np.asarray([invalid], dtype="float64"), domain, np)


def test_boundary_and_random_inputs_are_reproducible_and_inside_domain(reference):
    from collect_public_corpus import FAMILIES, bounds

    for family in FAMILIES:
        domain = {
            "closed_interval": bounds(family),
            "dtypes": ["float32", "float64"],
            "rank_max": 4,
            "elements_max": 4096,
        }
        records = reference.make_inputs(domain, 19, np)
        assert records == reference.make_inputs(domain, 19, np)
        assert len(records) == 64
        assert records != reference.make_inputs(domain, 20, np)
        for record in records:
            actual = np.asarray(record["values"], dtype=record["dtype"]).reshape(record["shape"])
            assert reference.valid_input(actual, domain, np)


def test_rounding_and_truncation_semantics_are_distinct(reference):
    assert reference.scalar_reference("trunc", -2) == -2
    assert reference.scalar_reference("trunc", -2.5) == -2
    assert reference.scalar_reference("floor", -2.5) == -3
    assert reference.scalar_reference("round", -2.5) == -2
    assert reference.scalar_reference("round", -3.5) == -4
