"""Run evidence probes for newly added development API groups."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import tensorflow as tf
import torch


OUTPUT = Path(__file__).with_name("sampling-trace.json")


def as_value(item: Any) -> Any:
    if isinstance(item, torch.Tensor):
        return item.detach().cpu().numpy().tolist()
    if isinstance(item, tf.Tensor):
        return item.numpy().tolist()
    return item


def probe_variance_default_correction() -> dict[str, Any]:
    values = [1.0, 2.0]
    source_input = torch.tensor(values, dtype=torch.float32)
    target_input = tf.constant(values, dtype=tf.float32)
    source = torch.var(source_input)
    naive = tf.math.reduce_variance(target_input)
    count = tf.cast(tf.size(target_input), target_input.dtype)
    adapted = naive * count / (count - 1.0)
    return {
        "property_id": "CCP-031",
        "counterexample_input": {"values": values, "dtype": "float32"},
        "source": {"value": as_value(source), "default_correction": 1},
        "naive_target": {"value": as_value(naive), "denominator": "N"},
        "adapted_target": {
            "value": as_value(adapted),
            "adapter": "population_variance * N / (N - 1)",
        },
        "naive_preserves": bool(np.isclose(as_value(source), as_value(naive))),
        "adapted_preserves": bool(np.isclose(as_value(source), as_value(adapted))),
        "violated_clause": "reduction-correction",
        "valid_domain": "finite floating tensors with reduced element count greater than one",
    }


def probe_softmax_axis() -> dict[str, Any]:
    values = [[0.0, 1.0, 2.0], [2.0, 1.0, 0.0]]
    source_input = torch.tensor(values, dtype=torch.float32)
    target_input = tf.constant(values, dtype=tf.float32)
    source = torch.nn.functional.softmax(source_input, dim=0)
    naive = tf.nn.softmax(target_input)
    adapted = tf.nn.softmax(target_input, axis=0)
    source_value = np.asarray(as_value(source))
    naive_value = np.asarray(as_value(naive))
    adapted_value = np.asarray(as_value(adapted))
    return {
        "property_id": "CCP-034",
        "counterexample_input": {"values": values, "dtype": "float32", "source_axis": 0},
        "source": {"value": source_value.tolist(), "axis_sums": source_value.sum(axis=0).tolist()},
        "naive_target": {
            "value": naive_value.tolist(),
            "default_axis": -1,
            "source_axis_sums": naive_value.sum(axis=0).tolist(),
        },
        "adapted_target": {
            "value": adapted_value.tolist(),
            "axis": 0,
            "axis_sums": adapted_value.sum(axis=0).tolist(),
        },
        "naive_preserves": bool(np.allclose(source_value, naive_value, atol=1e-7, rtol=0)),
        "adapted_preserves": bool(
            np.allclose(source_value, adapted_value, atol=1e-7, rtol=0)
        ),
        "violated_clause": "normalization-axis",
    }


def probe_softmax_computation_dtype() -> dict[str, Any]:
    values = [[0.0, 1.0, 2.0], [2.0, 1.0, 0.0]]
    source_input = torch.tensor(values, dtype=torch.float16)
    target_input = tf.constant(values, dtype=tf.float16)
    source = torch.nn.functional.softmax(source_input, dim=1, dtype=torch.float32)
    naive = tf.nn.softmax(target_input, axis=1)
    adapted = tf.nn.softmax(tf.cast(target_input, tf.float32), axis=1)
    return {
        "property_id": "CCP-035",
        "counterexample_input": {"values": values, "input_dtype": "float16", "axis": 1},
        "source": {"value": as_value(source), "output_dtype": str(source.dtype)},
        "naive_target": {"value": as_value(naive), "output_dtype": naive.dtype.name},
        "adapted_target": {"value": as_value(adapted), "output_dtype": adapted.dtype.name},
        "naive_preserves": naive.dtype == tf.float32,
        "adapted_preserves": adapted.dtype == tf.float32
        and bool(np.allclose(as_value(source), as_value(adapted), atol=1e-7, rtol=0)),
        "violated_clause": "computation-and-output-dtype",
    }


def main() -> None:
    probes = [
        probe_variance_default_correction(),
        probe_softmax_axis(),
        probe_softmax_computation_dtype(),
    ]
    result = {
        "dataset": "cosmit-candidate-certification-pilot",
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "torch": torch.__version__,
            "tensorflow": tf.__version__,
            "device": "CPU",
        },
        "probes": probes,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for probe in probes:
        assert not probe["naive_preserves"], probe["property_id"]
        assert probe["adapted_preserves"], probe["property_id"]
    print(f"wrote {OUTPUT}")
    print(f"probes={len(probes)} naive_refuted=3 adapted_supported=3")


if __name__ == "__main__":
    main()
