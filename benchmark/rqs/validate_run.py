"""Check budget accounting, artifact integrity and evidence gates without rerunning models."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def validate(run_directory: Path, check_current_sources: bool = False) -> dict[str, int]:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((run_directory / "manifest.json").read_text())
    summary = json.loads((run_directory / "summary.json").read_text())
    records = [
        json.loads(line) for line in (run_directory / "campaigns.jsonl").read_text().splitlines()
    ]
    expected = {
        (c["id"], policy, seed)
        for s in manifest["subjects"]
        for c in s["candidates"]
        for policy in manifest["policies"]
        for seed in manifest["seeds"]
    }
    observed = [(r["candidate_id"], r["policy"], r["seed"]) for r in records]
    assert len(set(observed)) == len(observed) and set(observed) == expected
    assert summary["campaign_count"] == len(records)
    assert manifest["independent_gold"] is False and manifest["holdout_opened"] is False
    if check_current_sources:
        for path, digest in manifest["source_hashes"].items():
            assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest, path
    for record in records:
        valid = [t for t in record["traces"] if t["outcome"] != "invalid-input"]
        assert len(valid) == record["executions"] <= record["budget"]
        if record["evidence_state"] == "refuted":
            confirms = [
                t for t in valid if t["phase"] == "confirm" and t["input"] == record["witness"]
            ]
            assert len(confirms) >= record["confirmation_count"]
            assert all(t["outcome"] == "violation" for t in confirms)
            assert record["failed_clause"] and record["root_cause"] == "undetermined"
        elif record["evidence_state"] == "supported-on-tested-inputs":
            assert valid and all(t["outcome"] == "pass" for t in record["traces"])
    for row in summary["results"]:
        selected = [
            r for r in records if r["policy"] == row["policy"] and r["origin"] == row["origin"]
        ]
        assert dict(Counter(r["evidence_state"] for r in selected)) == row["states"]
        assert sum(r["executions"] for r in selected) == row["executions"]
    for item in json.loads((run_directory / "minimization.json").read_text()):
        assert item["size"] <= item["original_size"] and len(item["attempts"]) <= item["budget"]
    for item in json.loads((run_directory / "conditions.json").read_text()):
        training = {json.dumps(x, sort_keys=True) for x in item["discovery_inputs"]}
        validation = {json.dumps(x, sort_keys=True) for x in item["validation_inputs"]}
        assert not training & validation
        for result in item["results"]:
            assert result["selection_used_validation"] is False
            assert result["validation_total"] == len(validation)
    return {
        "campaigns": len(records),
        "subjects": len(manifest["subjects"]),
        "candidate_executions": sum(r["executions"] for r in records),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--check-current-sources", action="store_true")
    args = parser.parse_args()
    print(validate(args.run_directory, args.check_current_sources))
