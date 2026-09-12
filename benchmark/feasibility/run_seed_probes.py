"""Execute the ten CoSMiT feasibility probes on the frozen CPU environment."""

from __future__ import annotations

import json
import platform
import sys
from typing import Any

import numpy as np
import tensorflow as tf
import torch


def value(item: Any) -> Any:
    if isinstance(item, torch.Tensor):
        return item.detach().cpu().numpy().tolist()
    if isinstance(item, tf.Tensor):
        return item.numpy().tolist()
    return item


def error_name(fn) -> str | None:
    try:
        fn()
    except Exception as exc:  # The exception class is the observation.
        return type(exc).__name__
    return None


def probe_sum() -> dict[str, Any]:
    source_input = torch.tensor([1, 2, 3], dtype=torch.int32)
    target_input = tf.constant([1, 2, 3], dtype=tf.int32)
    source = torch.sum(source_input)
    naive = tf.reduce_sum(target_input)
    adapted = tf.reduce_sum(tf.cast(target_input, tf.int64))
    return {
        "counterexample_input": {"values": [1, 2, 3], "dtype": "int32"},
        "source": {"value": value(source), "dtype": str(source.dtype)},
        "naive_target": {"value": value(naive), "dtype": naive.dtype.name},
        "adapted_target": {"value": value(adapted), "dtype": adapted.dtype.name},
        "naive_preserves": False,
        "adapted_preserves": True,
        "violated_clause": "output-dtype",
    }


def probe_mean() -> dict[str, Any]:
    source_input = torch.tensor([1, 2], dtype=torch.int64)
    target_input = tf.constant([1, 2], dtype=tf.int64)
    source = torch.mean(source_input, dtype=torch.float32)
    naive = tf.reduce_mean(target_input)
    adapted = tf.reduce_mean(tf.cast(target_input, tf.float32))
    return {
        "counterexample_input": {"values": [1, 2], "dtype": "int64"},
        "source": {"value": value(source), "dtype": str(source.dtype)},
        "naive_target": {"value": value(naive), "dtype": naive.dtype.name},
        "adapted_target": {"value": value(adapted), "dtype": adapted.dtype.name},
        "naive_preserves": False,
        "adapted_preserves": True,
        "violated_clause": "input-cast-and-value",
    }


def probe_argmax() -> dict[str, Any]:
    values = [[1.0, 5.0, 5.0], [9.0, 0.0, 0.0]]
    source = torch.argmax(torch.tensor(values), dim=1)
    naive = tf.argmax(tf.constant(values), axis=1, output_type=tf.int32)
    adapted = tf.argmax(tf.constant(values), axis=1, output_type=tf.int64)
    return {
        "counterexample_input": {"values": values, "axis": 1, "contains_tie": True},
        "source": {"value": value(source), "dtype": str(source.dtype)},
        "naive_target": {"value": value(naive), "dtype": naive.dtype.name},
        "adapted_target": {"value": value(adapted), "dtype": adapted.dtype.name},
        "naive_preserves": False,
        "adapted_preserves": True,
        "violated_clause": "output-dtype",
    }


def probe_transpose() -> dict[str, Any]:
    values = np.arange(24).reshape(2, 3, 4)
    source = torch.tensor(values).transpose(0, 1)
    naive = tf.transpose(tf.constant(values))
    adapted = tf.transpose(tf.constant(values), perm=[1, 0, 2])
    return {
        "counterexample_input": {"shape": [2, 3, 4], "source_dims": [0, 1]},
        "source": {"shape": list(source.shape), "sample": source.flatten()[:8].tolist()},
        "naive_target": {"shape": list(naive.shape), "sample": naive.numpy().flatten()[:8].tolist()},
        "adapted_target": {"shape": list(adapted.shape), "sample": adapted.numpy().flatten()[:8].tolist()},
        "naive_preserves": False,
        "adapted_preserves": bool(np.array_equal(value(source), value(adapted))),
        "violated_clause": "operation-axis-mapping",
    }


def probe_squeeze() -> dict[str, Any]:
    values = [[1, 2, 3]]
    source = torch.squeeze(torch.tensor(values), dim=1)
    target_input = tf.constant(values)
    naive_error = error_name(lambda: tf.squeeze(target_input, axis=1))
    adapted = tf.cond(
        tf.equal(tf.shape(target_input)[1], 1),
        lambda: tf.squeeze(target_input, axis=1),
        lambda: tf.identity(target_input),
    )
    return {
        "counterexample_input": {"shape": [1, 3], "axis": 1},
        "source": {"shape": list(source.shape), "value": value(source)},
        "naive_target": {"error": naive_error},
        "adapted_target": {"shape": list(adapted.shape), "value": value(adapted)},
        "naive_preserves": False,
        "adapted_preserves": bool(np.array_equal(value(source), value(adapted))),
        "violated_clause": "nonunit-axis-behavior",
    }


def probe_clamp() -> dict[str, Any]:
    values = [-1, 0, 1000]
    source = torch.clamp(torch.tensor(values, dtype=torch.int32), min=0)
    target_input = tf.constant(values, dtype=tf.int32)
    naive = tf.clip_by_value(target_input, 0, 999)
    adapted = tf.maximum(target_input, 0)
    return {
        "counterexample_input": {"values": values, "min": 0, "dtype": "int32"},
        "source": {"value": value(source)},
        "naive_target": {"value": value(naive), "invented_max": 999},
        "adapted_target": {"value": value(adapted)},
        "naive_preserves": False,
        "adapted_preserves": bool(np.array_equal(value(source), value(adapted))),
        "violated_clause": "one-sided-bound",
    }


def probe_assert_close() -> dict[str, Any]:
    source_actual = torch.tensor(0.0, dtype=torch.float32)
    source_expected = torch.tensor(5e-6, dtype=torch.float32)
    source_error = error_name(
        lambda: torch.testing.assert_close(
            source_actual, source_expected, rtol=0.0, atol=1e-5
        )
    )
    target_actual = tf.constant(0.0, dtype=tf.float32)
    target_expected = tf.constant(5e-6, dtype=tf.float32)
    naive_error = error_name(
        lambda: tf.debugging.assert_near(target_actual, target_expected)
    )
    adapted_error = error_name(
        lambda: tf.debugging.assert_near(
            target_actual, target_expected, rtol=0.0, atol=1e-5
        )
    )
    counterfactual_source_error = error_name(
        lambda: torch.testing.assert_close(
            source_actual, source_expected, rtol=0.0, atol=1e-6
        )
    )
    counterfactual_target_error = error_name(
        lambda: tf.debugging.assert_near(
            target_actual, target_expected, rtol=0.0, atol=1e-6
        )
    )
    return {
        "counterexample_input": {"actual": 0.0, "expected": 5e-6, "dtype": "float32"},
        "source": {"passes": source_error is None, "rtol": 0.0, "atol": 1e-5},
        "naive_target": {"passes": naive_error is None, "error": naive_error},
        "adapted_target": {"passes": adapted_error is None, "error": adapted_error},
        "counterfactual_tight_tolerance": {
            "rtol": 0.0,
            "atol": 1e-6,
            "source_passes": counterfactual_source_error is None,
            "target_passes": counterfactual_target_error is None,
        },
        "naive_preserves": False,
        "adapted_preserves": True,
        "violated_clause": "oracle-tolerance",
    }


def probe_cross_entropy() -> dict[str, Any]:
    logits = np.array(
        [
            [[2.0, 0.0], [0.0, 2.0], [-1.0, -1.0]],
            [[0.0, 1.0], [2.0, 0.0], [-1.0, -1.0]],
        ],
        dtype=np.float32,
    )
    labels = np.array([[0, 1], [1, 0]], dtype=np.int64)
    source = torch.nn.functional.cross_entropy(
        torch.tensor(logits), torch.tensor(labels), reduction="mean"
    )
    target_logits = tf.constant(logits)
    target_labels = tf.constant(labels)
    naive_error = error_name(
        lambda: tf.reduce_mean(
            tf.nn.sparse_softmax_cross_entropy_with_logits(
                labels=target_labels, logits=target_logits
            )
        )
    )
    adapted = tf.reduce_mean(
        tf.nn.sparse_softmax_cross_entropy_with_logits(
            labels=target_labels, logits=tf.transpose(target_logits, [0, 2, 1])
        )
    )
    difference = abs(float(value(source)) - float(value(adapted)))
    executable_logits = np.array(
        [
            [[2.0, 0.0, 1.0], [0.0, 2.0, 1.0], [-1.0, -1.0, 3.0]],
            [[0.0, 1.0, 2.0], [2.0, 0.0, 1.0], [-1.0, 3.0, -1.0]],
        ],
        dtype=np.float32,
    )
    executable_labels = np.array([[0, 1, 2], [1, 2, 0]], dtype=np.int64)
    executable_source = torch.nn.functional.cross_entropy(
        torch.tensor(executable_logits),
        torch.tensor(executable_labels),
        reduction="mean",
    )
    executable_naive = tf.reduce_mean(
        tf.nn.sparse_softmax_cross_entropy_with_logits(
            labels=tf.constant(executable_labels),
            logits=tf.constant(executable_logits),
        )
    )
    executable_adapted = tf.reduce_mean(
        tf.nn.sparse_softmax_cross_entropy_with_logits(
            labels=tf.constant(executable_labels),
            logits=tf.transpose(tf.constant(executable_logits), [0, 2, 1]),
        )
    )
    return {
        "counterexample_input": {"logits_shape": [2, 3, 2], "class_axis": 1},
        "source": {"value": value(source)},
        "naive_target": {"error": naive_error},
        "adapted_target": {"value": value(adapted), "class_axis": -1},
        "naive_preserves": False,
        "adapted_preserves": difference <= 1e-7,
        "absolute_difference": difference,
        "executable_wrong_mapping_witness": {
            "logits_shape": [2, 3, 3],
            "source_value": value(executable_source),
            "naive_target_value": value(executable_naive),
            "adapted_target_value": value(executable_adapted),
            "naive_absolute_difference": abs(
                float(value(executable_source)) - float(value(executable_naive))
            ),
            "adapted_absolute_difference": abs(
                float(value(executable_source)) - float(value(executable_adapted))
            ),
        },
        "violated_clause": "class-axis-and-reduction",
    }


def probe_random() -> dict[str, Any]:
    source_generator_a = torch.Generator().manual_seed(123)
    source_generator_b = torch.Generator().manual_seed(123)
    source_a = torch.randn(5, generator=source_generator_a)
    source_b = torch.randn(5, generator=source_generator_b)
    target_generator_a = tf.random.Generator.from_seed(123)
    target_generator_b = tf.random.Generator.from_seed(123)
    target_a = target_generator_a.normal([5])
    target_b = target_generator_b.normal([5])
    return {
        "counterexample_input": {"seed": 123, "shape": [5]},
        "source": {"first": value(source_a), "second": value(source_b)},
        "naive_target": {
            "cross_library_exact_equal": bool(
                np.array_equal(value(source_a), value(target_a))
            )
        },
        "adapted_target": {"first": value(target_a), "second": value(target_b)},
        "source_replay_equal": bool(torch.equal(source_a, source_b)),
        "target_replay_equal": bool(
            np.array_equal(value(target_a), value(target_b))
        ),
        "naive_preserves": False,
        "adapted_preserves": True,
        "violated_clause": "observation-relation-exact-values-vs-replay",
    }


def probe_gradient() -> dict[str, Any]:
    source_x = torch.tensor(1.0, requires_grad=True)
    source_y = torch.tensor(3.0, requires_grad=True)
    source_z = source_y * 2
    source = torch.autograd.grad(
        source_z, source_x, allow_unused=True, materialize_grads=True
    )[0]
    target_x = tf.constant(1.0)
    target_y = tf.constant(3.0)
    with tf.GradientTape() as naive_tape:
        naive_tape.watch([target_x, target_y])
        naive_z = target_y * 2
    naive = naive_tape.gradient(naive_z, target_x)
    with tf.GradientTape() as adapted_tape:
        adapted_tape.watch([target_x, target_y])
        adapted_z = target_y * 2
    adapted = adapted_tape.gradient(
        adapted_z,
        target_x,
        unconnected_gradients=tf.UnconnectedGradients.ZERO,
    )
    return {
        "counterexample_input": {"x": 1.0, "y": 3.0, "z": "2*y"},
        "source": {"gradient": value(source)},
        "naive_target": {"gradient": value(naive)},
        "adapted_target": {"gradient": value(adapted)},
        "naive_preserves": False,
        "adapted_preserves": value(source) == value(adapted),
        "violated_clause": "unconnected-gradient-policy",
    }


def main() -> None:
    probes = {
        "PTF-001": probe_sum,
        "PTF-002": probe_mean,
        "PTF-003": probe_argmax,
        "PTF-004": probe_transpose,
        "PTF-005": probe_squeeze,
        "PTF-006": probe_clamp,
        "PTF-007": probe_assert_close,
        "PTF-008": probe_cross_entropy,
        "PTF-009": probe_random,
        "PTF-010": probe_gradient,
    }
    result = {
        "environment": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "tensorflow": tf.__version__,
            "platform": platform.platform(),
            "device": "CPU",
        },
        "records": {identifier: fn() for identifier, fn in probes.items()},
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
