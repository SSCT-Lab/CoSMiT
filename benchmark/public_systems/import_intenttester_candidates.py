#!/usr/bin/env python3
"""Index published IntentTester candidates without copying unlicensed upstream code."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


RESULT_GLOB = "experiments/results/*/test_prompt_result/*.txt"
CODE_FENCE = re.compile(r"```(?P<language>[A-Za-z0-9_+-]*)\s*\n(?P<code>.*?)```", re.DOTALL)
TDL_FENCE = re.compile(r"Test Intent:\s*```json\s*\n(?P<tdl>.*?)```", re.DOTALL)
SAMPLE_PER_DIRECTION = 3


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def relative_to_workspace(path: Path, workspace: Path) -> str:
    return path.resolve().relative_to(workspace.resolve()).as_posix()


def extract_candidate(text: str) -> tuple[str, str | None, int]:
    fences = list(CODE_FENCE.finditer(text))
    if not fences:
        return "missing", None, 0
    first = fences[0]
    language = first.group("language").strip().lower() or "unknown"
    return language, first.group("code").strip() + "\n", len(fences)


def parse_tdl(prompt: str) -> tuple[dict[str, Any] | None, str | None]:
    match = TDL_FENCE.search(prompt)
    if match is None:
        return None, "missing-json-fence"
    try:
        value = json.loads(match.group("tdl"))
    except json.JSONDecodeError as exc:
        return None, f"json-error:{exc.lineno}:{exc.colno}"
    if not isinstance(value, dict):
        return None, "json-root-not-object"
    return value, None


def python_syntax(code: str) -> tuple[str, str | None, list[str]]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return "invalid", f"{exc.msg} at {exc.lineno}:{exc.offset}", []
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return "valid", None, sorted(roots)


def index_candidate(result_path: Path, repository: Path, workspace: Path) -> dict[str, Any]:
    direction = result_path.parents[1].name
    prompt_path = result_path.parent.parent / "test_prompt" / result_path.name
    raw = result_path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    language, code, fence_count = extract_candidate(text)
    prompt_exists = prompt_path.is_file()
    prompt_raw = prompt_path.read_bytes() if prompt_exists else b""
    prompt_text = prompt_raw.decode("utf-8", errors="replace") if prompt_exists else ""
    tdl, tdl_error = parse_tdl(prompt_text) if prompt_exists else (None, "missing-prompt")
    syntax_status = "not-checked"
    syntax_error = None
    python_import_roots: list[str] = []
    if language == "python" and code is not None:
        syntax_status, syntax_error, python_import_roots = python_syntax(code)

    metadata = tdl.get("metadata", {}) if tdl else {}
    assertions = tdl.get("assertions", []) if tdl else []
    execution_steps = tdl.get("executionSteps", []) if tdl else []
    candidate_id = f"IT-{direction}-{result_path.stem}"
    record: dict[str, Any] = {
        "candidate_id": candidate_id,
        "producer": "IntentTester",
        "origin": "public-system-output",
        "direction": direction,
        "raw_result_path": relative_to_workspace(result_path, workspace),
        "raw_result_sha256": sha256_bytes(raw),
        "prompt_path": relative_to_workspace(prompt_path, workspace) if prompt_exists else None,
        "prompt_sha256": sha256_bytes(prompt_raw) if prompt_exists else None,
        "language": language,
        "code_fence_count": fence_count,
        "code_sha256": sha256_bytes(code.encode()) if code is not None else None,
        "python_syntax": syntax_status,
        "python_syntax_error": syntax_error,
        "python_import_roots": python_import_roots,
        "tdl_status": "parsed" if tdl is not None else "invalid-or-missing",
        "tdl_error": tdl_error,
        "tdl_test_name": metadata.get("testName") if isinstance(metadata, dict) else None,
        "tdl_assertion_count": len(assertions) if isinstance(assertions, list) else None,
        "tdl_execution_step_count": len(execution_steps) if isinstance(execution_steps, list) else None,
        "source_property_status": "unreviewed",
        "execution_status": "not-run",
        "certification_status": "not-run",
    }
    return record


def select_sample(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    directions = sorted({str(record["direction"]) for record in records})
    for direction in directions:
        eligible = [
            record
            for record in records
            if record["direction"] == direction
            and record["code_sha256"] is not None
            and record["tdl_status"] == "parsed"
            and record["python_syntax"] != "invalid"
        ]
        eligible.sort(key=lambda record: (str(record["code_sha256"]), str(record["candidate_id"])))
        for record in eligible[:SAMPLE_PER_DIRECTION]:
            selected.append(
                {
                    "candidate_id": record["candidate_id"],
                    "direction": direction,
                    "language": record["language"],
                    "raw_result_path": record["raw_result_path"],
                    "prompt_path": record["prompt_path"],
                    "selection": "lowest-code-sha256",
                    "property_review": "pending",
                    "execution": "pending",
                }
            )
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path("tmp/intenttest-baseline"),
        help="Path to the pinned IntentTester checkout.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark/public_systems"),
    )
    args = parser.parse_args()

    workspace = Path.cwd().resolve()
    repository = args.repository.resolve()
    output_dir = args.output_dir.resolve()
    result_paths = sorted(repository.glob(RESULT_GLOB))
    if not result_paths:
        raise SystemExit(f"no IntentTester candidates found under {repository}")

    records = [index_candidate(path, repository, workspace) for path in result_paths]
    language_counts = Counter(str(record["language"]) for record in records)
    direction_counts = Counter(str(record["direction"]) for record in records)
    python_valid = sum(record["python_syntax"] == "valid" for record in records)
    python_invalid = sum(record["python_syntax"] == "invalid" for record in records)
    tdl_parsed = sum(record["tdl_status"] == "parsed" for record in records)
    commit = (
        repository.joinpath(".git", "HEAD").read_text(encoding="utf-8").strip()
        if not repository.joinpath(".git").is_dir()
        else None
    )

    manifest = {
        "dataset": "cosmit-public-system-candidates",
        "schema_version": "0.1",
        "producer": "IntentTester",
        "upstream_repository": "https://github.com/testmigrator/intenttest",
        "upstream_commit": commit,
        "license_status": "no-license-file-observed-do-not-copy-code",
        "candidate_count": len(records),
        "direction_counts": dict(sorted(direction_counts.items())),
        "language_counts": dict(sorted(language_counts.items())),
        "tdl_parsed": tdl_parsed,
        "python_syntax_valid": python_valid,
        "python_syntax_invalid": python_invalid,
        "records": records,
    }
    # Resolve a normal checkout's commit without shelling out or importing GitPython.
    head = repository / ".git" / "HEAD"
    if head.is_file():
        head_value = head.read_text(encoding="utf-8").strip()
        if head_value.startswith("ref: "):
            ref_path = repository / ".git" / head_value.removeprefix("ref: ")
            if ref_path.is_file():
                manifest["upstream_commit"] = ref_path.read_text(encoding="utf-8").strip()
        else:
            manifest["upstream_commit"] = head_value

    sample = {
        "dataset": "cosmit-public-system-candidate-review-sample",
        "schema_version": "0.1",
        "producer": "IntentTester",
        "selection_per_direction": SAMPLE_PER_DIRECTION,
        "records": select_sample(records),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "intenttester-candidates.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "intenttester-review-sample.yaml").write_text(
        yaml.safe_dump(sample, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    print(f"candidates={len(records)} directions={len(direction_counts)}")
    print(f"languages={dict(sorted(language_counts.items()))}")
    print(f"tdl_parsed={tdl_parsed}")
    print(f"python_syntax_valid={python_valid} python_syntax_invalid={python_invalid}")
    print(f"review_sample={len(sample['records'])}")


if __name__ == "__main__":
    main()
