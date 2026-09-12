#!/usr/bin/env python3
"""Read-only artifact audit and adversarial diagnostics; never executes candidates.

These synthetic cases diagnose checker false acceptance, NOT KATRER accuracy.
Outputs JSON to stdout; does not change historical experiment results.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    runner = load_module("audit_katrer_runner", "katrer_reproduction.py")
    checker = load_module("audit_katrer_checker", "katrer_property_check.py")
    source = Path(__file__).with_name("katrer-reproduction-results.json")
    data = json.loads(source.read_text())
    artifacts = []
    for record in data["records"]:
        latest = ROOT / record["artifact_directory"]
        origin = ROOT / record.get("candidate_origin_artifact", record["artifact_directory"])
        generation = json.loads((origin / "generation-response.json").read_text())
        judgement = json.loads((latest / "judgement-response.json").read_text())
        prompt = (origin / "generation-prompt.txt").read_text()
        artifacts.append({
            "case_id": record["case_id"],
            "candidate_summary_hash_matches": runner.sha256_text(record["candidate_code"]) == record["candidate_sha256"],
            "candidate_file_hash_matches": digest(latest / "candidate.py") == record["candidate_sha256"],
            "candidate_origin_hash_matches": digest(origin / "candidate.py") == record["candidate_sha256"],
            "generation_extract_matches": runner.clean_python_block(runner.response_text(generation)) == record["candidate_code"],
            "generation_prompt_hash_matches": runner.sha256_text(prompt.rstrip("\n")) == record["generation_prompt_sha256"],
            "generation_finish_reason": generation["choices"][0].get("finish_reason"),
            "judgement_finish_reason": judgement["choices"][0].get("finish_reason"),
            "judgement_matches": runner.judgement_value(runner.response_text(judgement)) == record["llm_consistency_judgement"],
            "historical_status": record["property_check"],
            "audited_evidence_state": "undetermined",
        })
    adversarial = [
        ("wrong_library", "KATRER-NC-001", """import cupy as cp
import numpy as np
import pytest
def test_wrong_library():
    with pytest.raises(ValueError):
        np.fft.fft([1], n=0)
"""),
        ("unreachable_fft", "KATRER-NC-001", """import cupy as cp
import pytest
def test_unreachable():
    with pytest.raises(ValueError):
        raise ValueError('not raised by FFT')
        cp.fft.fft(cp.array([1]), n=0)
"""),
        ("dead_boundary_calls", "KATRER-NC-002", """import cupy as cp
def test_dead_code():
    if False:
        cp.fft.irfft([1], n=1)
        cp.fft.hfft([1], n=1)
        cp.fft.irfft([1], n=10)
"""),
        ("missing_oracles_wrong_comparison", "KATRER-NC-003", """import cupy as cp
def test_no_oracle():
    if False:
        cp.squeeze(a)
        cp.squeeze(b)
        cp.squeeze(c)
        cp.squeeze(d)
        cp.reshape(a, (1,))
        cp.reshape(b, (1,))
        cp.reshape(c, (1,))
        res.ndim != 0
        cp.ndarray
"""),
    ]
    failures = [{
        "id": name, "case_id": case_id, "synthetic_code": code,
        "expected_clause_preserved": False,
        "legacy_clause_preserved": checker.candidate_clause_check(case_id, code)[0],
        "legacy_target_binding_observed": runner.target_binding_status(code, "cupy"),
    } for name, case_id, code in adversarial]
    output = {
        "audit_date": "2026-09-08", "network_calls": 0,
        "historical_result_sha256": digest(source),
        "checker_sha256": digest(Path(checker.__file__)),
        "runner_sha256": digest(Path(runner.__file__)),
        "manifest_hash_matches": digest(ROOT / data["manifest_path"]) == data["manifest_sha256"],
        "artifacts": artifacts, "synthetic_checker_diagnostics": failures,
        "empty_text_syntax_status": runner.syntax_status("")[0],
        "unused_import_binding_status": runner.target_binding_status("import cupy\n", "cupy"),
        "interpretation": "False acceptance diagnoses heuristics only; it is not an observed defect in the three generated candidates. Historical supported status is not justified by this checker.",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
