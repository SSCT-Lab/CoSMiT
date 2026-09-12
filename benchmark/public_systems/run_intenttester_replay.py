#!/usr/bin/env python3
"""Replay reviewed IntentTester candidates and independent simplejson witnesses."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
PROPERTY_LEDGER = ROOT / "intenttester-properties.yaml"
OUTPUT = ROOT / "intenttester-replay.json"
VENV_PYTHON = WORKSPACE / "tmp/public-system-envs/intenttester-python/bin/python"
CODE_FENCE = re.compile(r"```python\s*\n(?P<code>.*?)```", re.DOTALL | re.IGNORECASE)
TIMEOUT_SECONDS = 10

REFERENCE_EXPRESSIONS = {
    "IT-PROP-001": """simplejson.loads('[1, -1.0e6, "abc", [1,2,3], {"abc":123}, true, false]')[4]['abc']""",
    "IT-PROP-002": """simplejson.loads('{"key": 1}').get('key') is not None""",
    "IT-PROP-003": "simplejson.dumps([True], separators=(',', ':'))",
    "IT-PROP-004": "capture_exception(lambda: simplejson.loads('Test is a test..blah blah'))",
}


def extract_python(path: Path) -> str:
    match = CODE_FENCE.search(path.read_text(encoding="utf-8", errors="replace"))
    if match is None:
        raise ValueError(f"missing Python code fence: {path}")
    return match.group("code").strip() + "\n"


def imported_roots(code: str) -> list[str]:
    tree = ast.parse(code)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return sorted(roots)


def sandbox_profile(temporary_directory: Path) -> str:
    escaped = str(temporary_directory.resolve()).replace('"', '\\"')
    return " ".join(
        [
            "(version 1)",
            "(allow default)",
            "(deny network*)",
            "(deny file-write*)",
            '(allow file-write* (literal "/dev/null"))',
            f'(allow file-write* (subpath "{escaped}"))',
        ]
    )


def run_sandboxed(command: list[str], temporary_directory: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["sandbox-exec", "-p", sandbox_profile(temporary_directory), *command],
        cwd=temporary_directory,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
        "passed": completed.returncode == 0,
    }


def run_candidate(code: str, temporary_directory: Path) -> dict[str, Any]:
    candidate_file = temporary_directory / "candidate.py"
    candidate_file.write_text(code, encoding="utf-8")
    return run_sandboxed([str(VENV_PYTHON), str(candidate_file)], temporary_directory)


def run_reference(property_id: str, temporary_directory: Path) -> dict[str, Any]:
    expression = REFERENCE_EXPRESSIONS[property_id]
    script = (
        "import json, simplejson\n"
        "def capture_exception(function):\n"
        "    try:\n"
        "        function()\n"
        "    except Exception as exception:\n"
        "        return type(exception).__name__\n"
        "    return None\n"
        f"value = {expression}\n"
        "print(json.dumps({'value': value, 'simplejson_version': simplejson.__version__}, sort_keys=True))\n"
    )
    reference_file = temporary_directory / "reference.py"
    reference_file.write_text(script, encoding="utf-8")
    result = run_sandboxed([str(VENV_PYTHON), str(reference_file)], temporary_directory)
    if result["passed"]:
        result["observation"] = json.loads(str(result["stdout"]).strip())
    return result


def main() -> None:
    if not VENV_PYTHON.is_file():
        raise SystemExit(f"missing replay environment: {VENV_PYTHON}")
    ledger = yaml.safe_load(PROPERTY_LEDGER.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for record in ledger["records"]:
        candidate_path = WORKSPACE / record["candidate_path"]
        code = extract_python(candidate_path)
        imports = imported_roots(code)
        with tempfile.TemporaryDirectory(prefix="cosmit-intenttester-") as directory:
            temporary_directory = Path(directory)
            candidate_result = run_candidate(code, temporary_directory)
            reference_result = run_reference(record["property_id"], temporary_directory)
        target_observed = "simplejson" in imports
        expected = record["property"]["oracle"]["expected"]
        reference_oracle_satisfied = bool(
            reference_result["passed"]
            and reference_result.get("observation", {}).get("value") == expected
        )
        evidence_state = (
            "refuted"
            if reference_oracle_satisfied and not target_observed
            else "undetermined"
        )
        results.append(
            {
                "property_id": record["property_id"],
                "candidate_id": record["candidate_id"],
                "candidate_imports": imports,
                "candidate_self_test": candidate_result,
                "independent_target_witness": reference_result,
                "reference_oracle_satisfied": reference_oracle_satisfied,
                "target_module_observed": target_observed,
                "qualification_obligation": {
                    "clause": "target-operation-binding",
                    "state": "supported" if target_observed else "refuted",
                    "evidence": "static import analysis over the complete candidate code",
                },
                "candidate_evidence_state": evidence_state,
                "diagnosis": [] if target_observed else ["invalid-mapping", "target-library-bypass"],
                "gold_eligible": False,
            }
        )

    output = {
        "dataset": ledger["dataset"],
        "schema_version": ledger["schema_version"],
        "environment": ledger["environment"],
        "results": results,
    }
    OUTPUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate_passes = sum(result["candidate_self_test"]["passed"] for result in results)
    references_pass = sum(result["independent_target_witness"]["passed"] for result in results)
    reference_oracles = sum(result["reference_oracle_satisfied"] for result in results)
    bypasses = sum(not result["target_module_observed"] for result in results)
    print(f"cases={len(results)} candidate_self_tests_pass={candidate_passes}")
    print(f"independent_target_witnesses_pass={references_pass}")
    print(f"reference_oracles_satisfied={reference_oracles}")
    print(f"target_library_bypass={bypasses}")


if __name__ == "__main__":
    main()
