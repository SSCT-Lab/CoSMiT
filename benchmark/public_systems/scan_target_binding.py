#!/usr/bin/env python3
"""Scan unambiguous target-package bindings in published IntentTester candidates."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "intenttester-candidates.json"
OUTPUT = ROOT / "intenttester-target-binding-scan.json"

# These directions have one unambiguous Python package name for the target.
TARGET_MODULES = {
    "gson-to-simplejson": "simplejson",
    "nanojson-to-simplejson": "simplejson",
    "jfiveparse-to-domonic": "domonic",
    "jsoup-to-domonic": "domonic",
    "threetenbp-to-maya": "maya",
    "time4j-to-maya": "maya",
}


def classify(record: dict[str, Any], target_module: str) -> str:
    if record["language"] != "python":
        return "non-python-output"
    if record["python_syntax"] != "valid":
        return "python-syntax-invalid"
    imports = set(record["python_import_roots"])
    if target_module in imports:
        return "target-module-import-observed"
    if target_module == "simplejson" and "json" in imports:
        return "stdlib-json-imported-target-module-absent"
    if "target_repository" in imports or "your_module" in imports:
        return "placeholder-import-target-module-absent"
    return "target-module-import-absent"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records = manifest["records"]
    summaries: list[dict[str, Any]] = []
    for direction, target_module in TARGET_MODULES.items():
        selected = [record for record in records if record["direction"] == direction]
        counts = Counter(classify(record, target_module) for record in selected)
        summaries.append(
            {
                "direction": direction,
                "target_module": target_module,
                "candidate_count": len(selected),
                "classification_counts": dict(sorted(counts.items())),
            }
        )

    simplejson = [
        item for item in summaries if item["target_module"] == "simplejson"
    ]
    simplejson_total = sum(item["candidate_count"] for item in simplejson)
    simplejson_valid = sum(
        item["classification_counts"].get("stdlib-json-imported-target-module-absent", 0)
        + item["classification_counts"].get("target-module-import-absent", 0)
        + item["classification_counts"].get("placeholder-import-target-module-absent", 0)
        + item["classification_counts"].get("target-module-import-observed", 0)
        for item in simplejson
    )
    simplejson_target_observed = sum(
        item["classification_counts"].get("target-module-import-observed", 0)
        for item in simplejson
    )
    output = {
        "dataset": "cosmit-intenttester-target-binding-scan",
        "schema_version": "0.1",
        "analysis_scope": "static imports in complete Python code fences",
        "interpretation": (
            "Absence is a qualification signal, not a semantic verdict, until source-property "
            "alignment and independent review are complete."
        ),
        "summaries": summaries,
        "simplejson_aggregate": {
            "candidate_count": simplejson_total,
            "syntax_valid_python_count": simplejson_valid,
            "target_module_import_observed": simplejson_target_observed,
        },
    }
    OUTPUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"simplejson_candidates={simplejson_total} "
        f"syntax_valid_python={simplejson_valid} "
        f"target_import_observed={simplejson_target_observed}"
    )
    for summary in summaries:
        print(summary["direction"], summary["classification_counts"])


if __name__ == "__main__":
    main()
