import importlib
import json
import sys
from pathlib import Path

import pytest


@pytest.fixture
def ports():
    path = str(Path(__file__).resolve().parents[1] / "benchmark/baselines")
    sys.path.insert(0, path)
    yield importlib.import_module("verification_ports")
    sys.path.pop(0)


def test_unknown_constraint_is_not_satisfaction(ports):
    schema = {
        "inputs": {"required": ["x"]},
        "constraints": {"x": {"shape": ["[N,C]"], "range": ["[0,MAX]"]}},
    }
    args = {"x": {"kind": "tensor", "dtype": "float32", "values": [[1.0]]}}
    assert ports.check_docter(schema, args)["state"] == "undetermined"
    assert ports.check_docter(schema, {})["state"] == "violated"


def test_tensor_dtype_is_not_inferred_from_integer_looking_values(ports):
    schema = {"constraints": {"x": {"dtype": ["int"]}}}
    args = {"x": {"kind": "tensor", "dtype": "float32", "values": [1, 2]}}
    assert ports.check_docter(schema, args)["state"] == "violated"
    args["x"]["dtype"] = "int64"
    assert ports.check_docter(schema, args)["state"] == "satisfied"


def test_docter_alias_dtypes_and_partial_fields(ports):
    schema = {
        "constraints": {"x": {"dtype": ["tf.float32"], "tensor_t": ["tf.tensor", "SparseTensor"]}}
    }
    args = {"x": {"kind": "tensor", "dtype": "float32", "values": [1.0]}}
    assert ports.check_docter(schema, args)["state"] == "satisfied"
    schema["constraints"]["x"]["shape"] = ["[N]"]
    assert ports.check_docter(schema, args)["state"] == "undetermined"


@pytest.mark.parametrize(
    "answer",
    [
        '{"valid":"true","reason":"ok"}',
        '{"valid":1,"reason":"ok"}',
        "True, no problem",
        '{"reason":"ok"}',
    ],
)
def test_model_boolean_parser_rejects_ambiguous_answers(ports, answer):
    with pytest.raises((ValueError, TypeError)):
        ports.parse_model_answer(answer, "intenttester-target-api")


def test_missing_model_stage_cannot_accept(ports):
    assert ports.aggregate_checks([True, None]) == "undetermined"
    assert ports.aggregate_checks([True, False]) == "rejected"
    assert ports.aggregate_checks([True, True]) == "accepted"
    assert ports.aggregate_checks([]) == "undetermined"


def test_mutation_preserves_shape_dtype_and_does_not_edit_source(ports):
    source = {"x": {"kind": "tensor", "dtype": "float32", "values": [[2.0, -3.0], [4.0, 9.0]]}}
    before = json.dumps(source)
    a = ports.mutate_inputs(source, 1)
    assert a == ports.mutate_inputs(source, 1)
    assert ports.tensor_shape(a["x"]["values"]) == [2, 2]
    assert a["x"]["dtype"] == "float32"
    assert json.dumps(source) == before


def test_prompt_packet_does_not_leak_reference_or_verifier_output(ports, monkeypatch):
    monkeypatch.setattr(ports, "java_prompt", lambda *a: "{testIntent} {testCode} {intentTest}")
    case = {
        "id": "C001",
        "source": {"code": "source"},
        "target": {"code": "target"},
        "inputs": [],
        "contract": {"description": "finite abs", "clauses": ["shape"]},
        "gold": "SECRET_GOLD",
        "origin": "SECRET_MUTANT_ORIGIN",
    }
    trace = {
        "status": "completed",
        "verdicts": "SECRET_VERDICT",
        "records": [
            {
                "input_index": 0,
                "repeat": 0,
                "source": {"value": 1},
                "target": {"value": 2},
                "clause_results": "SECRET_COSMIT",
                "dllens_agrees": "SECRET_DLLENS",
            }
        ],
    }
    jobs = ports.prepare_llm_jobs(case, trace)
    text = json.dumps(jobs)
    assert "SECRET_" not in text
    assert len(jobs) == 5 and len({j["job_id"] for j in jobs}) == 5
    assert "observations" not in jobs[0]["prompt"]
    assert "observations" in jobs[1]["prompt"]
    assert all("import tensorflow as tf" in job["prompt"] for job in jobs)


def test_unstable_or_unconfirmed_witness_does_not_refute(ports):
    runner = importlib.import_module("run_experiment")

    def row(repeat, value):
        return {
            "input_index": 0,
            "repeat": repeat,
            "status": "executed",
            "dllens_agrees": False,
            "source": {"value": [1.0], "dtype": "float32", "shape": [1]},
            "target": {"value": [value], "dtype": "float32", "shape": [1], "calls": ["tf.abs"]},
            "clause_results": [{"clause_id": "value", "outcome": "violation"}],
        }

    for rows in [[row(0, 2.0)], [row(0, 2.0), row(1, 2.0), row(2, 3.0)]]:
        assert (
            runner.summarize({"status": "completed", "records": rows})["cosmit-registered-clauses"]
            == "undetermined"
        )
    rows = [row(i, 2.0) for i in range(3)]
    assert (
        runner.summarize({"status": "completed", "records": rows})["cosmit-registered-clauses"]
        == "refuted"
    )


def test_invalid_source_is_not_reported_as_target_violation(ports):
    runner = importlib.import_module("run_experiment")
    result = runner.summarize(
        {"status": "completed", "records": [{"status": "invalid-source-test"}]}
    )
    assert set(result.values()) == {"invalid-source-test"}
    assert set(runner.summarize({"status": "timeout"}).values()) == {"undetermined"}


def test_summary_rejects_results_from_another_prompt_version(ports, tmp_path, monkeypatch):
    summary = importlib.import_module("summarize_experiment")
    monkeypatch.setattr(
        summary, "prepare_llm_jobs", lambda *a: [{"job_id": "j1", "prompt_sha256": "expected"}]
    )
    experiment = tmp_path / "experiment"
    (experiment / "C001").mkdir(parents=True)
    (experiment / "packet.json").write_text(json.dumps({"cases": [{"id": "C001"}]}))
    (experiment / "C001/record.json").write_text(json.dumps({"execution": {}}))
    llm = tmp_path / "llm"
    llm.mkdir()
    (llm / "selected-jobs.json").write_text(
        json.dumps([{"job_id": "j1", "prompt_sha256": "different"}])
    )
    with pytest.raises(ValueError, match="different candidate/context"):
        summary.summarize(experiment, tmp_path / "report", llm, None)
