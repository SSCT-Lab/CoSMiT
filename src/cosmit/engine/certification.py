"""Budgeted, clause-level execution for trusted, parameterized candidate programs.

Positive results describe only the explicitly recorded input set, never an
unexplored domain. This module does not execute arbitrary submitted test files.
"""

from __future__ import annotations

import copy
import math
import time
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from typing import Any

Input = dict[str, Any]


@dataclass(frozen=True)
class Observation:
    value: Any = None
    dtype: str | None = None
    shape: tuple[int, ...] | None = None
    error: str | None = None
    infrastructure_error: bool = False


@dataclass(frozen=True)
class Property:
    property_id: str
    clause_id: str
    oracle: str
    precondition: Callable[[Input], bool]
    source: Callable[[Input], Observation]
    atol: float = 0.0
    rtol: float = 0.0

    def __post_init__(self) -> None:
        if self.oracle not in {"value", "dtype", "shape", "exception", "outcome"}:
            raise ValueError(f"unsupported oracle: {self.oracle}")
        if self.atol < 0 or self.rtol < 0:
            raise ValueError("negative tolerances")


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    execute: Callable[[Input], Observation]
    origin: str
    code_sha256: str
    # This is external registration evidence, not inferred from an import.
    target_binding: str = "unverified"


def equal_values(left: Any, right: Any, atol: float, rtol: float) -> bool:
    if isinstance(left, list) or isinstance(right, list):
        return (
            isinstance(left, list)
            and isinstance(right, list)
            and len(left) == len(right)
            and all(equal_values(x, y, atol, rtol) for x, y in zip(left, right))
        )
    if left is None or right is None:
        return left is right
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (float, int)) and isinstance(right, (float, int)):
        # NaN needs its own declared oracle, not an implicit equal_nan policy.
        if not math.isfinite(left) or not math.isfinite(right):
            return False
        return abs(left - right) <= atol + rtol * abs(left)
    return type(left) is type(right) and left == right


def observe(operation: Callable[[Input], Observation], probe: Input) -> Observation:
    try:
        result = operation(copy.deepcopy(probe))
        if not isinstance(result, Observation):
            raise TypeError("operation must return Observation")
        return result
    except Exception as error:  # noqa: BLE001 - callback boundary; unknown errors abstain.
        # Unknown exceptions are infrastructure/residual errors, not semantic
        # witnesses. Framework-specific expected errors must be caught in the
        # registered observer and returned explicitly as observations.
        return Observation(error=type(error).__name__, infrastructure_error=True)


def evaluate(prop: Property, candidate: Candidate, probe: Input) -> dict[str, Any]:
    started = time.perf_counter()
    result: dict[str, Any] = {"input": copy.deepcopy(probe), "clause_id": prop.clause_id}
    try:
        valid = bool(prop.precondition(copy.deepcopy(probe)))
    except Exception:  # noqa: BLE001 - a failed domain predicate cannot validate an input.
        valid = False
    if not valid:
        return {**result, "outcome": "invalid-input", "seconds": time.perf_counter() - started}
    source = observe(prop.source, probe)
    target = observe(candidate.execute, probe)
    result.update(source=asdict(source), target=asdict(target))
    if candidate.target_binding != "registered-target-operation":
        outcome = "undetermined"
        result["unresolved_obligation"] = "target-operation-binding"
    elif (
        source.infrastructure_error
        or target.infrastructure_error
        or source.error
        and prop.oracle != "exception"
    ):
        outcome = "undetermined"
    elif prop.oracle == "exception":
        # Exception observers normalize names only under an explicit mapping.
        outcome = "pass" if source.error == target.error else "violation"
    elif target.error:
        outcome = "violation"
    elif prop.oracle == "dtype":
        outcome = (
            "undetermined"
            if source.dtype is None or target.dtype is None
            else ("pass" if source.dtype == target.dtype else "violation")
        )
    elif prop.oracle == "shape":
        outcome = (
            "undetermined"
            if source.shape is None or target.shape is None
            else ("pass" if source.shape == target.shape else "violation")
        )
    else:
        if prop.oracle == "value" and source.value is None:
            outcome = "undetermined"
        elif source.shape != target.shape:
            outcome = "violation"
        else:
            outcome = (
                "pass"
                if equal_values(source.value, target.value, prop.atol, prop.rtol)
                else "violation"
            )
    result.update(outcome=outcome, seconds=time.perf_counter() - started)
    return result


def certify(
    prop: Property,
    candidate: Candidate,
    probes: Iterable[Input],
    budget: int,
    confirmations: int = 2,
) -> dict[str, Any]:
    """All confirmation pairs consume the same candidate-execution budget.

    One execution unit = one source/candidate pair. Invalid proposed inputs do
    not execute either program, but are logged and capped to prevent hangs.
    """
    if budget < 1 or confirmations < 1:
        raise ValueError("positive execution budget and confirmations required")
    traces: list[dict[str, Any]] = []
    executions = 0
    state = "undetermined"
    witness = None
    for index, probe in enumerate(probes):
        if executions >= budget or index >= budget * 10:
            break
        trace = evaluate(prop, candidate, probe)
        trace["phase"] = "search"
        traces.append(trace)
        if trace["outcome"] == "invalid-input":
            continue
        executions += 1
        if trace["outcome"] != "violation":
            continue
        if executions + confirmations > budget:
            break
        stable = True
        for _ in range(confirmations):
            repeated = evaluate(prop, candidate, probe)
            repeated["phase"] = "confirm"
            traces.append(repeated)
            executions += 1
            # Preserve observed behavior as well as the classification.
            stable = (
                stable
                and repeated["outcome"] == "violation"
                and (
                    repeated.get("source") == trace.get("source")
                    and repeated.get("target") == trace.get("target")
                )
            )
        if stable:
            state, witness = "refuted", copy.deepcopy(probe)
            break
    if traces and all(t["outcome"] == "pass" for t in traces):
        state = "supported-on-tested-inputs"
    return {
        "property_id": prop.property_id,
        "candidate_id": candidate.candidate_id,
        "origin": candidate.origin,
        "candidate_code_sha256": candidate.code_sha256,
        "evidence_state": state,
        "executions": executions,
        "budget": budget,
        "confirmation_count": confirmations,
        "witness": witness,
        "failed_clause": prop.clause_id if state == "refuted" else None,
        "root_cause": "undetermined",
        "target_binding": candidate.target_binding,
        "scope": "recorded inputs only; no domain-wide certificate",
        "seconds": sum(t["seconds"] for t in traces),
        "traces": traces,
    }


def input_size(probe: Input) -> int:
    def count(value: Any) -> int:
        if isinstance(value, list):
            return sum(count(item) for item in value)
        return 1

    return sum(count(v) for v in probe.values())


def minimize(
    prop: Property,
    candidate: Candidate,
    witness: Input,
    shrink: Callable[[Input], Iterable[Input]],
    budget: int = 24,
) -> dict[str, Any]:
    """Greedy reduction under a supplied input grammar; not global minimality."""
    current = copy.deepcopy(witness)
    attempts: list[dict[str, Any]] = []
    while len(attempts) + 2 <= budget:
        improved = False
        for smaller in shrink(current):
            if len(attempts) + 2 > budget:
                break
            if input_size(smaller) >= input_size(current):
                continue
            trace = evaluate(prop, candidate, smaller)
            attempts.append(trace)
            if trace["outcome"] != "violation":
                continue
            confirm = evaluate(prop, candidate, smaller)
            attempts.append(confirm)
            if (
                confirm["outcome"] == "violation"
                and trace.get("source") == confirm.get("source")
                and trace.get("target") == confirm.get("target")
            ):
                current, improved = copy.deepcopy(smaller), True
                break
        if not improved:
            break
    return {
        "input": current,
        "original_size": input_size(witness),
        "size": input_size(current),
        "attempts": attempts,
        "budget": budget,
        "minimality": "greedy grammar-relative only",
    }


def check_conditions(
    prop: Property,
    candidate: Candidate,
    conditions: dict[str, Callable[[Input], bool]],
    discovery: list[Input],
    validation: list[Input],
    min_retained: int = 3,
    min_fraction: float = 0.2,
) -> list[dict[str, Any]]:
    """Select on discovery only, then assess on disjoint validation inputs.

    Validation failures are reported, never used to choose another condition.
    No global boundary truth or human diagnosis is inferred here.
    """
    if any(x == y for x in discovery for y in validation):
        raise ValueError("condition discovery/validation inputs overlap")
    train = [evaluate(prop, candidate, x) for x in discovery]
    if not any(t["outcome"] == "violation" for t in train):
        return []
    results = []
    for name, predicate in conditions.items():
        kept = [t for t in train if predicate(t["input"])]
        if (
            len(kept) < min_retained
            or len(kept) < len(train) * min_fraction
            or any(t["outcome"] != "pass" for t in kept)
        ):
            continue
        heldout = [evaluate(prop, candidate, x) for x in validation]
        retained = [t for t in heldout if predicate(t["input"])]
        successes = sum(t["outcome"] == "pass" for t in retained)
        # This is finite-sample behavior, not independently annotated boundaries.
        results.append(
            {
                "condition": name,
                "discovery_retained": len(kept),
                "validation_total": len(heldout),
                "validation_retained": len(retained),
                "validation_passes": successes,
                "validation_violations": sum(t["outcome"] == "violation" for t in retained),
                "state": "supported-on-validation-inputs"
                if len(retained) >= min_retained
                and len(retained) >= len(heldout) * min_fraction
                and successes == len(retained)
                else "undetermined-or-refuted",
                "validation_traces": heldout,
                "selection_used_validation": False,
                "scope": "sample only; no universal condition or boundary accuracy claim",
            }
        )
    return results
