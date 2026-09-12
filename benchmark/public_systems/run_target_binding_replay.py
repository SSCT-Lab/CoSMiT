"""User-data-isolated replay of the existing sample with dynamic API probes.

Public candidate code is copied only into temporary directories, never into the
persistent result bundle. Runtime files are whitelisted inside user-data denial
rules; standard OS files remain readable. This is not a complete security proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from run_intenttester_execution_sample import extract_code
from run_intenttester_replay import VENV_PYTHON

ROOT = Path(__file__).resolve().parents[2]


def sandbox(directory: Path) -> str:
    allowed = [
        directory.resolve(),
        VENV_PYTHON.parent.parent.resolve(),
        Path("/Library/Frameworks/Python.framework"),
        Path("/System/Library"),
        Path("/usr/lib"),
        Path("/System/Volumes/Preboot/Cryptexes/OS/usr/lib"),
        Path("/System/Volumes/Preboot/Cryptexes/OS/System/Library"),
        Path("/private/preboot/Cryptexes/OS/usr/lib"),
        Path("/private/var/db/dyld"),
        Path("/dev/null"),
        Path("/dev/urandom"),
        Path("/dev/random"),
    ]
    rules = [
        "(version 1)",
        "(allow default)",
        "(deny network*)",
        "(deny file-write*)",
        '(deny file-read-data (subpath "/Users") (subpath "/private/var/folders") (subpath "/Volumes"))',
        '(allow file-write* (literal "/dev/null"))',
    ]
    for path in allowed:
        escaped = str(path).replace('"', '\\"')
        rules.append(f'(allow file-read-data (subpath "{escaped}"))')
    escaped = str(directory.resolve()).replace('"', '\\"')
    rules.append(f'(allow file-write* (subpath "{escaped}"))')
    return " ".join(rules)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("intenttester-dynamic-binding-2026-09-09.json"),
    )
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    original = json.loads(
        Path(__file__).with_name("intenttester-execution-sample.json").read_text()
    )
    manifest = json.loads(Path(__file__).with_name("intenttester-candidates.json").read_text())
    by_id = {r["candidate_id"]: r for r in manifest["records"]}
    worker = Path(__file__).with_name("target_binding_worker.py").read_text()
    env = {k: v for k, v in os.environ.items() if k in {"PATH", "LANG", "LC_ALL", "TMPDIR"}}
    env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
    results = []
    for selected in original["results"]:
        record = by_id[selected["candidate_id"]]
        code = extract_code(record)
        with tempfile.TemporaryDirectory(prefix="cosmit-binding-") as temporary:
            directory = Path(temporary)
            (directory / "candidate.py").write_text(code)
            (directory / "worker.py").write_text(worker)
            try:
                process = subprocess.run(
                    [
                        "sandbox-exec",
                        "-p",
                        sandbox(directory),
                        str(VENV_PYTHON),
                        "-I",
                        str(directory / "worker.py"),
                        str(directory / "candidate.py"),
                    ],
                    env=env,
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                marker = [
                    line.removeprefix("COSMIT_BINDING_JSON=")
                    for line in process.stdout.splitlines()
                    if line.startswith("COSMIT_BINDING_JSON=")
                ]
                execution = (
                    json.loads(marker[-1])
                    if marker
                    else {
                        "status": "worker-error",
                        "exit_code": process.returncode,
                        "stderr": process.stderr[-1500:],
                    }
                )
            except subprocess.TimeoutExpired:
                execution = {"status": "timeout"}
        results.append(
            {
                "candidate_id": record["candidate_id"],
                "code_sha256": record["code_sha256"],
                "instrumented_execution": execution,
                "gold_eligible": False,
            }
        )
    output = {
        "scope": "existing deterministic 40-candidate sample; instrumented entry points only",
        "not_a_semantic_certificate": True,
        "observer_coverage": [
            "loads",
            "load",
            "dumps",
            "dump",
            "JSONDecoder.decode",
            "JSONEncoder.encode",
        ],
        "sandbox": "network/writes denied; user homes, private user caches and mounted volumes denied except runtime and task temp; minimal environment; standard OS files readable",
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "worker_sha256": hashlib.sha256(worker.encode()).hexdigest(),
        "results": results,
    }
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    successful_workers = sum("pytest_exit_code" in r["instrumented_execution"] for r in results)
    observed = sum(bool(r["instrumented_execution"].get("target_calls")) for r in results)
    print(f"workers={successful_workers}/40, observed selected target calls={observed}/40")


if __name__ == "__main__":
    main()
