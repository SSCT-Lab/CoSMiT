#!/usr/bin/env python3
"""Execute a deterministic sample of published Python candidates in a write-limited sandbox."""

from __future__ import annotations

import json
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from run_intenttester_replay import VENV_PYTHON, run_sandboxed


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
MANIFEST = ROOT / "intenttester-candidates.json"
OUTPUT = ROOT / "intenttester-execution-sample.json"
CODE_FENCE = re.compile(r"```python\s*\n(?P<code>.*?)```", re.DOTALL | re.IGNORECASE)
DIRECTIONS = ("gson-to-simplejson", "nanojson-to-simplejson")
SAMPLE_PER_DIRECTION = 20


def extract_code(record: dict[str, Any]) -> str:
    path = WORKSPACE / record["raw_result_path"]
    match = CODE_FENCE.search(path.read_text(encoding="utf-8", errors="replace"))
    if match is None:
        raise ValueError(f"missing Python fence: {path}")
    return match.group("code").strip() + "\n"


def failure_category(result: dict[str, Any]) -> str:
    if result["passed"]:
        return "passed"
    output = f"{result['stdout']}\n{result['stderr']}"
    if "ModuleNotFoundError" in output or "ImportError" in output:
        return "import-error"
    if "AssertionError" in output or "FAILED" in output or "FAILURES" in output:
        return "assertion-or-test-failure"
    if result.get("status") == "timeout":
        return "timeout"
    return "runtime-or-collection-error"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    all_records = manifest["records"]
    selected: list[dict[str, Any]] = []
    for direction in DIRECTIONS:
        eligible = [
            record
            for record in all_records
            if record["direction"] == direction and record["python_syntax"] == "valid"
        ]
        eligible.sort(key=lambda record: (record["code_sha256"], record["candidate_id"]))
        selected.extend(eligible[:SAMPLE_PER_DIRECTION])

    results: list[dict[str, Any]] = []
    for record in selected:
        code = extract_code(record)
        with tempfile.TemporaryDirectory(prefix="cosmit-intenttester-batch-") as directory:
            temporary_directory = Path(directory)
            candidate_file = temporary_directory / "candidate.py"
            candidate_file.write_text(code, encoding="utf-8")
            execution = run_sandboxed(
                [str(VENV_PYTHON), "-m", "pytest", "-q", str(candidate_file)],
                temporary_directory,
            )
        category = failure_category(execution)
        results.append(
            {
                "candidate_id": record["candidate_id"],
                "direction": record["direction"],
                "code_sha256": record["code_sha256"],
                "python_import_roots": record["python_import_roots"],
                "target_module_observed": "simplejson" in record["python_import_roots"],
                "execution": execution,
                "execution_category": category,
                "property_status": "unreviewed",
            }
        )

    category_counts = Counter(record["execution_category"] for record in results)
    output = {
        "dataset": "cosmit-intenttester-execution-sample",
        "schema_version": "0.1",
        "selection": "20 lowest code SHA-256 syntax-valid Python candidates per direction",
        "directions": list(DIRECTIONS),
        "environment": {
            "target_module": "simplejson",
            "target_version": "3.20.1",
            "sandbox": "network and non-temporary writes denied",
        },
        "category_counts": dict(sorted(category_counts.items())),
        "results": results,
    }
    OUTPUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"executed={len(results)} categories={dict(sorted(category_counts.items()))}")
    print(f"target_module_observed={sum(r['target_module_observed'] for r in results)}")


if __name__ == "__main__":
    main()
