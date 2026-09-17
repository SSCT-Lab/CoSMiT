import importlib
import json
import sys
from pathlib import Path

import pytest


@pytest.fixture
def modules():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark/baselines"))
    yield (
        importlib.import_module("merge_primary_batches"),
        importlib.import_module("finalize_background_campaign"),
    )
    sys.path.pop(0)


def make_batch(path, status="completed"):
    from verification_ports import digest

    path.mkdir()
    job = {
        "job_id": "a" * 20,
        "case_id": "C001",
        "kind": "direct-llm",
        "prompt": "fixed",
        "prompt_sha256": digest("fixed"),
    }
    record = {k: job[k] for k in ["job_id", "case_id", "kind", "prompt_sha256"]}
    record.update(status=status)
    if status == "completed":
        record["parsed"] = {"verdict": "preserved", "reason": "fixed"}
    for name, data in [
        ("selected-jobs.json", [job]),
        ("summary.json", {}),
        ("configuration.json", {}),
        (job["job_id"] + ".json", record),
    ]:
        (path / name).write_text(json.dumps(data))
    return job, record


def test_duplicate_logical_requests_are_never_silently_counted_twice(modules, tmp_path):
    merge, _ = modules
    a, b = tmp_path / "a", tmp_path / "b"
    make_batch(a)
    make_batch(b)
    with pytest.raises(ValueError, match="Overlapping"):
        merge.merge([a, b], tmp_path / "union")
    assert not (tmp_path / "union").exists()


def test_successful_primary_request_cannot_be_replaced_by_retry(modules, tmp_path):
    _, finalizer = modules
    primary, retry = tmp_path / "primary", tmp_path / "retry"
    make_batch(primary)
    make_batch(retry)
    with pytest.raises(ValueError, match="successful primary"):
        finalizer.retry_view(primary, retry, tmp_path / "view")


def test_retry_view_preserves_primary_failure_and_provenance(modules, tmp_path):
    _, finalizer = modules
    primary, retry, view = tmp_path / "primary", tmp_path / "retry", tmp_path / "view"
    job, _ = make_batch(primary, "failed")
    make_batch(retry)
    finalizer.retry_view(primary, retry, view)
    original = json.loads((primary / (job["job_id"] + ".json")).read_text())
    derived = json.loads((view / (job["job_id"] + ".json")).read_text())
    assert original["status"] == "failed"
    assert derived["status"] == "completed" and derived["primary_status"] == "failed"
    assert derived["retry_file_sha256"] and derived["primary_file_sha256"]
