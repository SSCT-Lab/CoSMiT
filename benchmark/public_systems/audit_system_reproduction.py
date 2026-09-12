#!/usr/bin/env python3
"""Run bounded, unmodified reproduction checks for IntentTester and KATRER."""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
INTENTTESTER = WORKSPACE / "tmp/intenttest-baseline"
KATRER = WORKSPACE / "tmp/katrer-baseline"
OUTPUT = ROOT / "system-reproduction-trace.json"
JDK_HOME = Path(os.environ["JAVA_HOME"]) if os.environ.get("JAVA_HOME") else None
KATRER_PYTHON = (
    Path(os.environ["COSMIT_KATRER_PYTHON"])
    if os.environ.get("COSMIT_KATRER_PYTHON")
    else None
)


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "status": "timeout",
            "exit_code": None,
            "stdout": (exc.stdout or "")[-12000:],
            "stderr": (exc.stderr or "")[-12000:],
        }
    return {
        "command": command,
        "status": "passed" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-12000:],
    }


def git_commit(repository: Path) -> str:
    result = run(["git", "rev-parse", "HEAD"], repository)
    if result["exit_code"] != 0:
        raise RuntimeError(f"cannot resolve commit for {repository}")
    return str(result["stdout"]).strip()


def katrer_generation_calls(path: Path) -> dict[str, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    definitions = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "call_llm_api"
        for node in ast.walk(tree)
    )
    calls = sum(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "call_llm_api"
        for node in ast.walk(tree)
    )
    return {"definitions": definitions, "calls": calls}


def zenodo_status() -> dict[str, Any]:
    curl = shutil.which("curl")
    if curl is None:
        return {"status": "not-checked", "reason": "curl-unavailable"}
    result = run([curl, "-fsSL", "https://zenodo.org/api/records/17140838"], WORKSPACE)
    if result["exit_code"] != 0:
        return {"status": "unavailable", "trace": result}
    data = json.loads(str(result["stdout"]))
    metadata = data.get("metadata", {})
    return {
        "status": "checked",
        "record": 17140838,
        "access_right": metadata.get("access_right"),
        "public_file_count": len(data.get("files", [])),
        "doi": metadata.get("doi"),
    }


def main() -> None:
    if not INTENTTESTER.is_dir() or not KATRER.is_dir():
        raise SystemExit("pinned upstream checkouts are required under tmp/")

    maven = shutil.which("mvn")
    intent_env = os.environ.copy()
    if JDK_HOME is not None:
        intent_env["JAVA_HOME"] = str(JDK_HOME)
        intent_env["PATH"] = f"{JDK_HOME / 'bin'}:{intent_env.get('PATH', '')}"
    intent_build = (
        run([maven, "-q", "-DskipTests", "package"], INTENTTESTER, intent_env)
        if maven and JDK_HOME is not None and JDK_HOME.is_dir()
        else {"status": "not-run", "reason": "maven-or-jdk20-unavailable"}
    )
    intent_python = run(
        [
            str(Path(shutil.which("python3") or "python3")),
            "python/step1_test_intent/tdl_main.py",
        ],
        INTENTTESTER,
    )

    katrer_scripts = sorted((KATRER / "KATRER").glob("*.py"))
    katrer_compile = (
        run([str(KATRER_PYTHON), "-m", "py_compile", *map(str, katrer_scripts)], KATRER)
        if KATRER_PYTHON is not None and KATRER_PYTHON.is_file()
        else {"status": "not-run", "reason": "python312-environment-unavailable"}
    )
    katrer_query = (
        run([str(KATRER_PYTHON), "QueryAns.py"], KATRER / "KATRER")
        if KATRER_PYTHON is not None and KATRER_PYTHON.is_file()
        else {"status": "not-run", "reason": "python312-environment-unavailable"}
    )
    query_source = (KATRER / "KATRER/QueryAns.py").read_text(encoding="utf-8")

    result = {
        "dataset": "cosmit-public-system-reproduction",
        "schema_version": "0.1",
        "date": "2026-09-04",
        "IntentTester": {
            "commit": git_commit(INTENTTESTER),
            "license_file_present": any(INTENTTESTER.glob("LICENSE*")),
            "published_candidate_count": len(
                list(INTENTTESTER.glob("experiments/results/*/test_prompt_result/*.txt"))
            ),
            "jdk": "20.0.1",
            "unmodified_maven_build": intent_build,
            "unmodified_python_tdl_entry": intent_python,
            "pipeline_status": "externally-blocked",
        },
        "KATRER": {
            "commit": git_commit(KATRER),
            "license_file_present": any(KATRER.glob("LICENSE*")),
            "python_syntax_compile": katrer_compile,
            "unmodified_query_ans_entry": katrer_query,
            "generation_function_usage": katrer_generation_calls(KATRER / "KATRER/QueryAns.py"),
            "hardcoded_path2_occurrences": query_source.count("/path2/"),
            "placeholder_api_key_present": "Your_API_Key_Here" in query_source,
            "main_output_directories_present": {
                name: (KATRER / name).is_dir() for name in ("res_gpu", "judge_ans", "test_res")
            },
            "zenodo": zenodo_status(),
            "pipeline_status": "externally-blocked",
        },
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"IntentTester build={intent_build['status']} python_tdl={intent_python['status']}")
    print(f"KATRER compile={katrer_compile['status']} query={katrer_query['status']}")
    print(
        "KATRER outputs="
        + json.dumps(result["KATRER"]["main_output_directories_present"], sort_keys=True)
    )
    print(f"KATRER Zenodo={result['KATRER']['zenodo']}")


if __name__ == "__main__":
    main()
