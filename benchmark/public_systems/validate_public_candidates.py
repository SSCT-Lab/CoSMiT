#!/usr/bin/env python3
"""Validate provenance and leakage boundaries for imported public candidates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
MANIFEST = ROOT / "intenttester-candidates.json"
SAMPLE = ROOT / "intenttester-review-sample.yaml"
PROPERTIES = ROOT / "intenttester-properties.yaml"
REPLAY = ROOT / "intenttester-replay.json"
BINDING_SCAN = ROOT / "intenttester-target-binding-scan.json"
EXECUTION_SAMPLE = ROOT / "intenttester-execution-sample.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sample = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    properties = yaml.safe_load(PROPERTIES.read_text(encoding="utf-8"))
    replay = json.loads(REPLAY.read_text(encoding="utf-8"))
    binding_scan = json.loads(BINDING_SCAN.read_text(encoding="utf-8"))
    execution_sample = json.loads(EXECUTION_SAMPLE.read_text(encoding="utf-8"))
    records = manifest["records"]
    ids = [record["candidate_id"] for record in records]
    assert len(ids) == len(set(ids)) == manifest["candidate_count"]
    assert manifest["producer"] == "IntentTester"
    assert manifest["license_status"] == "no-license-file-observed-do-not-copy-code"
    assert all(record["origin"] == "public-system-output" for record in records)
    assert all(record["source_property_status"] == "unreviewed" for record in records)
    assert all(record["certification_status"] == "not-run" for record in records)

    by_id = {record["candidate_id"]: record for record in records}
    sample_ids = [record["candidate_id"] for record in sample["records"]]
    assert len(sample_ids) == len(set(sample_ids))
    assert set(sample_ids) <= set(by_id)
    assert len(sample_ids) == 3 * len(manifest["direction_counts"])

    for record in records:
        raw_path = WORKSPACE / record["raw_result_path"]
        assert raw_path.is_file(), raw_path
        assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == record["raw_result_sha256"]
        if record["prompt_path"] is not None:
            prompt_path = WORKSPACE / record["prompt_path"]
            assert prompt_path.is_file(), prompt_path
            assert hashlib.sha256(prompt_path.read_bytes()).hexdigest() == record["prompt_sha256"]

    property_records = properties["records"]
    property_ids = [record["property_id"] for record in property_records]
    assert len(property_ids) == len(set(property_ids))
    assert all(record["candidate_id"] in by_id for record in property_records)
    assert properties["gold_eligible"] is False
    source_checkout = WORKSPACE / "tmp/public-system-sources/nanojson"
    assert source_checkout.is_dir()
    replay_records = replay["results"]
    assert {record["property_id"] for record in replay_records} == set(property_ids)
    assert all(record["reference_oracle_satisfied"] for record in replay_records)
    assert sum(record["candidate_self_test"]["passed"] for record in replay_records) == 3
    assert all(not record["target_module_observed"] for record in replay_records)
    assert all(record["candidate_evidence_state"] == "refuted" for record in replay_records)
    simplejson_scan = binding_scan["simplejson_aggregate"]
    assert simplejson_scan["candidate_count"] == 680
    assert simplejson_scan["syntax_valid_python_count"] == 659
    assert simplejson_scan["target_module_import_observed"] == 0
    execution_records = execution_sample["results"]
    assert len(execution_records) == 40
    assert all(record["candidate_id"] in by_id for record in execution_records)
    assert all(not record["target_module_observed"] for record in execution_records)

    print(
        f"candidates={len(records)} sample={len(sample_ids)} "
        f"qualified_properties={len(property_records)}"
    )
    print(f"commit={manifest['upstream_commit']}")
    print("public candidate validation: PASS")


if __name__ == "__main__":
    main()
