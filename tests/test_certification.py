import pytest

from cosmit.engine.certification import (
    Candidate,
    Observation,
    Property,
    certify,
    check_conditions,
    equal_values,
    evaluate,
    minimize,
)


def setup_pair(target=lambda x: Observation(value=x["x"] + 1)):
    prop = Property(
        "P", "value-clause", "value", lambda x: x["x"] >= 0, lambda x: Observation(value=x["x"])
    )
    return prop, Candidate(
        "M", target, "researcher-mutant", "fixture", "registered-target-operation"
    )


def test_counterexample_confirmation_costs_budget():
    prop, candidate = setup_pair()
    result = certify(prop, candidate, [{"x": 1}], 3)
    assert result["evidence_state"] == "refuted"
    assert result["executions"] == 3
    assert result["failed_clause"] == "value-clause"
    assert result["root_cause"] == "undetermined"
    assert certify(prop, candidate, [{"x": 1}], 2)["evidence_state"] == "undetermined"


def test_empty_and_invalid_probes_do_not_vacuously_support():
    prop, candidate = setup_pair()
    assert certify(prop, candidate, [], 5)["evidence_state"] == "undetermined"
    assert certify(prop, candidate, [{"x": -1}], 5)["executions"] == 0
    assert evaluate(prop, candidate, {"bad": 1})["outcome"] == "invalid-input"


def test_no_domain_wide_positive_and_input_copy_isolation():
    def mutate(x):
        x["x"] = 100
        return Observation(value=1)

    prop, candidate = setup_pair(mutate)
    probe = {"x": 1}
    assert certify(prop, candidate, [probe], 3)["evidence_state"] == "supported-on-tested-inputs"
    assert probe == {"x": 1}


def test_infrastructure_error_is_not_refutation():
    def broken(x):
        raise ModuleNotFoundError("runtime absent")

    prop, candidate = setup_pair(broken)
    assert evaluate(prop, candidate, {"x": 1})["outcome"] == "undetermined"


def test_nonreproducible_difference_is_not_certified():
    counter = iter(range(20))
    prop, candidate = setup_pair(lambda x: Observation(value=next(counter) + 20))
    assert certify(prop, candidate, [{"x": 1}], 5)["evidence_state"] == "undetermined"


def test_dtype_clause_does_not_silently_become_value_clause():
    prop = Property(
        "P", "dtype", "dtype", lambda x: True, lambda x: Observation(value=1, dtype="int64")
    )
    candidate = Candidate(
        "M",
        lambda x: Observation(value=1, dtype="int32"),
        "fixture",
        "x",
        "registered-target-operation",
    )
    assert evaluate(prop, candidate, {})["outcome"] == "violation"


def test_shape_checks_do_not_allow_broadcasting():
    prop = Property(
        "P", "value", "value", lambda x: True, lambda x: Observation(value=[1], shape=(1,))
    )
    candidate = Candidate(
        "M", lambda x: Observation(value=1, shape=()), "fixture", "x", "registered-target-operation"
    )
    assert evaluate(prop, candidate, {})["outcome"] == "violation"
    assert not equal_values(float("nan"), float("nan"), 0, 0)


def test_minimization_requires_smaller_valid_stable_witness():
    prop = Property(
        "P", "value", "value", lambda x: len(x["values"]) >= 2, lambda x: Observation(value=0)
    )
    candidate = Candidate(
        "M", lambda x: Observation(value=1), "fixture", "x", "registered-target-operation"
    )
    result = minimize(
        prop, candidate, {"values": [1, 2, 3, 4]}, lambda x: [{"values": x["values"][:-1]}], 10
    )
    assert result["input"] == {"values": [1, 2]}
    assert len(result["attempts"]) <= 10


def test_refinement_uses_disjoint_validation_and_rejects_tiny_domain():
    prop, candidate = setup_pair(lambda x: Observation(value=x["x"] if x["x"] < 5 else -1))
    conditions = {"x<5": lambda x: x["x"] < 5, "x==0": lambda x: x["x"] == 0}
    discovery = [{"x": x} for x in range(10)]
    validation = [{"x": x + 0.5} for x in range(10)]
    result = check_conditions(prop, candidate, conditions, discovery, validation)
    assert len(result) == 1 and result[0]["condition"] == "x<5"
    assert result[0]["validation_passes"] == 5
    assert result[0]["selection_used_validation"] is False
    with pytest.raises(ValueError):
        check_conditions(prop, candidate, conditions, discovery, discovery)


def test_unknown_oracle_and_bad_budget_fail_fast():
    with pytest.raises(ValueError):
        Property("P", "C", "made-up", lambda x: True, lambda x: Observation())
    prop, candidate = setup_pair()
    with pytest.raises(ValueError):
        certify(prop, candidate, [], 0)


def test_matching_value_without_target_registration_is_unresolved():
    prop, _ = setup_pair()
    candidate = Candidate("bypass", lambda x: Observation(value=x["x"]), "fixture", "x")
    record = evaluate(prop, candidate, {"x": 1})
    assert record["outcome"] == "undetermined"
    assert record["unresolved_obligation"] == "target-operation-binding"
