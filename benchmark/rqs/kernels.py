"""Executable development fixtures derived from existing seed/pilot mappings.

These are parameterized researcher implementations, NOT extracted KATRER or
IntentTester tests. The actual functions below are executed for every probe.
No mutant labels are exposed to the checker or probe generator.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import tensorflow as tf
import torch

from cosmit.engine.certification import Observation


def observation(value: Any) -> Observation:
    if value is None:
        return Observation()
    if isinstance(value, torch.Tensor):
        array = value.detach().cpu().numpy()
    elif isinstance(value, tf.Tensor):
        array = value.numpy()
    else:
        array = np.asarray(value)
    return Observation(value=array.tolist(), dtype=str(array.dtype), shape=tuple(array.shape))


def source(family: str, probe: dict[str, Any]) -> Observation:
    x = torch.tensor(probe["values"], dtype=getattr(torch, probe["dtype"]))
    if family == "sum":
        y = torch.sum(x)
    elif family == "mean":
        y = torch.mean(x, dtype=torch.float32)
    elif family == "argmax":
        y = torch.argmax(x, dim=1)
    elif family == "transpose":
        y = x.transpose(0, 1)
    elif family == "squeeze":
        y = torch.squeeze(x, dim=1)
    elif family == "clamp":
        y = torch.clamp(x, min=0)
    elif family == "assert_close":
        try:
            torch.testing.assert_close(x[0], x[1], rtol=0.0, atol=1e-5)
            return observation(True)
        except AssertionError:
            return observation(False)
    elif family == "cross_entropy":
        y = torch.nn.functional.cross_entropy(x, torch.tensor(probe["labels"], dtype=torch.int64))
    elif family == "gradient":
        a, b = x[0].clone().requires_grad_(True), x[1].clone().requires_grad_(True)
        y = torch.autograd.grad(b * 2, a, allow_unused=True, materialize_grads=True)[0]
    elif family == "variance":
        y = torch.var(x)
    elif family == "softmax_axis":
        y = torch.nn.functional.softmax(x, dim=0)
    elif family == "softmax_dtype":
        y = torch.nn.functional.softmax(x, dim=1, dtype=torch.float32)
    else:
        raise ValueError(f"unregistered source family {family}")
    return observation(y)


def target(family: str, adapted: bool, probe: dict[str, Any]) -> Observation:
    x = tf.constant(probe["values"], dtype=getattr(tf, probe["dtype"]))
    try:
        if family == "sum":
            y = tf.reduce_sum(tf.cast(x, tf.int64) if adapted else x)
        elif family == "mean":
            y = tf.reduce_mean(tf.cast(x, tf.float32) if adapted else x)
        elif family == "argmax":
            y = tf.argmax(x, axis=1, output_type=tf.int64 if adapted else tf.int32)
        elif family == "transpose":
            y = tf.transpose(x, perm=[1, 0, 2] if adapted else None)
        elif family == "squeeze":
            y = tf.identity(x) if adapted and x.shape[1] != 1 else tf.squeeze(x, axis=1)
        elif family == "clamp":
            y = tf.maximum(x, 0) if adapted else tf.clip_by_value(x, 0, 999)
        elif family == "assert_close":
            try:
                if adapted:
                    tf.debugging.assert_near(x[0], x[1], rtol=0.0, atol=1e-5)
                else:
                    tf.debugging.assert_near(x[0], x[1])
                return observation(True)
            except tf.errors.InvalidArgumentError:
                return observation(False)
        elif family == "cross_entropy":
            y = tf.reduce_mean(
                tf.nn.sparse_softmax_cross_entropy_with_logits(
                    logits=tf.transpose(x, [0, 2, 1]) if adapted else x,
                    labels=tf.constant(probe["labels"], dtype=tf.int64),
                )
            )
        elif family == "gradient":
            a, b = x[0], x[1]
            with tf.GradientTape() as tape:
                tape.watch([a, b])
                z = b * 2
            y = tape.gradient(
                z,
                a,
                unconnected_gradients=(
                    tf.UnconnectedGradients.ZERO if adapted else tf.UnconnectedGradients.NONE
                ),
            )
        elif family == "variance":
            y = tf.math.reduce_variance(x)
            if adapted:
                n = tf.cast(tf.size(x), x.dtype)
                y = y * n / (n - 1)
        elif family == "softmax_axis":
            y = tf.nn.softmax(x, axis=0 if adapted else -1)
        elif family == "softmax_dtype":
            y = tf.nn.softmax(tf.cast(x, tf.float32) if adapted else x, axis=1)
        else:
            raise ValueError(f"unregistered target family {family}")
        return observation(y)
    except (tf.errors.InvalidArgumentError, ValueError, TypeError) as error:
        # These are operation outcomes on inputs already accepted by P and S.
        # Missing runtimes/OOM/unknown observer errors propagate as infrastructure.
        return Observation(error=type(error).__name__)
