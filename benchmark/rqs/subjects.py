"""Frozen development-only domains and source-clause-driven probe templates."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import kernels
import numpy as np

from cosmit.engine.certification import Candidate, Input, Property


@dataclass(frozen=True)
class Subject:
    prop: Property
    family: str
    original: Input
    shapes: tuple[tuple[int, ...], ...]
    candidates: tuple[Candidate, ...]


SPECS = [
    ("CCP-001", "sum", "output-dtype", "dtype", "int32", [1, 2, 3], ((1,), (3,), (5,))),
    ("CCP-004", "mean", "input-cast-and-value", "value", "int64", [1, 2], ((2,), (3,), (5,))),
    (
        "CCP-007",
        "argmax",
        "output-dtype",
        "dtype",
        "float32",
        [[1, 5, 5], [9, 0, 0]],
        ((1, 2), (2, 3)),
    ),
    (
        "CCP-010",
        "transpose",
        "operation-axis-mapping",
        "value",
        "int64",
        np.arange(24).reshape(2, 3, 4).tolist(),
        ((1, 1, 1), (2, 3, 4), (2, 2, 2)),
    ),
    (
        "CCP-013",
        "squeeze",
        "nonunit-axis-behavior",
        "value",
        "int32",
        [[1, 2, 3]],
        ((1, 1), (1, 3), (2, 1), (2, 3)),
    ),
    ("CCP-016", "clamp", "one-sided-bound", "value", "int32", [-1, 0, 1000], ((1,), (3,), (5,))),
    ("CCP-019", "assert_close", "oracle-tolerance", "outcome", "float32", [0, 5e-6], ((2,),)),
    (
        "CCP-022",
        "cross_entropy",
        "class-axis-and-reduction",
        "value",
        "float32",
        [[[2, 0, 1], [0, 2, 1], [-1, -1, 3]], [[0, 1, 2], [2, 0, 1], [-1, 3, -1]]],
        ((1, 2, 2), (2, 3, 3)),
    ),
    ("CCP-028", "gradient", "unconnected-gradient-policy", "value", "float32", [1, 3], ((2,),)),
    ("CCP-031", "variance", "reduction-correction", "value", "float32", [1, 2], ((2,), (3,), (5,))),
    (
        "CCP-034",
        "softmax_axis",
        "normalization-axis",
        "value",
        "float32",
        [[0, 1, 2], [2, 1, 0]],
        ((1, 1), (2, 3), (3, 2)),
    ),
    (
        "CCP-035",
        "softmax_dtype",
        "computation-and-output-dtype",
        "dtype",
        "float16",
        [[0, 1, 2], [2, 1, 0]],
        ((1, 2), (2, 3)),
    ),
]


def valid_input(probe: Input, dtype: str, shapes: tuple[tuple[int, ...], ...], family: str) -> bool:
    try:
        x = np.asarray(probe["values"])
        if probe["dtype"] != dtype or tuple(x.shape) not in shapes or not np.isfinite(x).all():
            return False
        if dtype.startswith("int") and (np.any(x != np.floor(x)) or np.any(abs(x) > 4096)):
            return False
        if not dtype.startswith("int") and np.any(abs(x) > 10):
            return False
        if family == "cross_entropy":
            labels = np.asarray(probe["labels"])
            return bool(
                labels.shape == (x.shape[0], x.shape[2])
                and np.all(labels == np.floor(labels))
                and np.all(labels >= 0)
                and np.all(labels < x.shape[1])
            )
        return True
    except (ValueError, KeyError, TypeError):
        return False


def subjects() -> list[Subject]:
    result = []
    kernel_hash = hashlib.sha256(Path(kernels.__file__).read_bytes()).hexdigest()
    for pid, family, clause, oracle, dtype, values, shapes in SPECS:
        original = {"values": values, "dtype": dtype}
        if family == "cross_entropy":
            original["labels"] = [[0, 1, 2], [1, 2, 0]]
        prop = Property(
            pid,
            clause,
            oracle,
            partial(valid_input, dtype=dtype, shapes=shapes, family=family),
            partial(kernels.source, family),
            atol=1e-7,
        )
        variants = []
        for adapted, suffix, origin in [
            (True, "REF", "evidence-derived-reference"),
            (False, "MUT", "researcher-mutant"),
        ]:
            code_hash = hashlib.sha256(
                json.dumps([kernel_hash, family, adapted]).encode()
            ).hexdigest()
            variants.append(
                Candidate(
                    f"{pid}-{suffix}",
                    partial(kernels.target, family, adapted),
                    origin,
                    code_hash,
                    "registered-target-operation",
                )
            )
        result.append(Subject(prop, family, original, shapes, tuple(variants)))
    return result


def make_probe(
    subject: Subject, rng: np.random.Generator, shape: tuple[int, ...], mode: str
) -> Input:
    size = int(np.prod(shape))
    integer = subject.original["dtype"].startswith("int")
    if mode == "zero":
        values = np.zeros(shape)
    elif mode == "boundary":
        values = rng.choice([-2048, -1, 0, 1, 2048] if integer else [-1, 0, 1], size=size).reshape(
            shape
        )
    elif mode == "asymmetric":
        values = np.arange(size).reshape(shape) % 5 - 2
    else:
        values = (
            rng.integers(-2048, 2049, size=size).reshape(shape)
            if integer
            else rng.uniform(-1, 1, size=shape)
        )
    if integer:
        values = values.astype(np.int64)
    result = {"values": values.tolist(), "dtype": subject.original["dtype"]}
    if subject.family == "cross_entropy":
        result["labels"] = rng.integers(0, shape[1], size=(shape[0], shape[2])).tolist()
    return result


def probes(subject: Subject, policy: str, seed: int, count: int) -> list[Input]:
    if policy == "original":
        # Historical hand-selected feasibility witness, not an official regression input.
        return [copy.deepcopy(subject.original)]
    if policy not in {"random", "boundary", "clause-aware"}:
        raise ValueError("unknown policy")
    rng = np.random.default_rng(seed)
    generated = []
    for index in range(count):
        shape = subject.shapes[int(rng.integers(len(subject.shapes)))]
        mode = "random" if policy == "random" else "boundary"
        if policy == "clause-aware":
            # Dispatch on the source oracle/clause, never on candidate or label.
            clause = subject.prop.clause_id
            if "axis" in clause:
                shape = max(subject.shapes, key=lambda s: len(set(s)))
                mode = "asymmetric"
            elif subject.prop.oracle == "dtype":
                mode = "zero"
            elif clause == "reduction-correction":
                mode = "asymmetric"
        probe = make_probe(subject, rng, shape, mode)
        if policy == "clause-aware" and subject.prop.clause_id == "oracle-tolerance":
            # Read the explicit source atol=1e-5 from the registered subject contract.
            probe["values"] = [0.0, [5e-6, 2e-5, 0.0][index % 3]]
        generated.append(probe)
    return generated


def shrink(probe: Input) -> Iterator[Input]:
    """Try slicing every dimension; P rejects illegal ranks/shapes/labels."""
    array = np.asarray(probe["values"])
    for axis in range(array.ndim):
        if array.shape[axis] <= 1:
            continue
        candidate = copy.deepcopy(probe)
        candidate["values"] = np.take(array, [0], axis=axis).tolist()
        if "labels" in candidate:
            labels = np.asarray(candidate["labels"])
            if axis == 0:
                labels = labels[:1]
            elif axis == 2:
                labels = labels[:, :1]
            candidate["labels"] = labels.tolist()
        yield candidate
