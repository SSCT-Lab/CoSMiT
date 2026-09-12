import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "benchmark/public_systems"


@pytest.mark.skipif(shutil.which("sandbox-exec") is None, reason="macOS sandbox required")
@pytest.mark.parametrize("module,expect_calls", [("simplejson", True), ("json", False)])
def test_instrumentation_positive_and_bypass_control(tmp_path, module, expect_calls):
    sys.path.insert(0, str(MODULE_DIR))
    try:
        spec = importlib.util.spec_from_file_location(
            "binding_replay_controls", MODULE_DIR / "run_target_binding_replay.py"
        )
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
    finally:
        sys.path.pop(0)
    if not runner.VENV_PYTHON.exists():
        pytest.skip("published-output replay environment absent")
    (tmp_path / "worker.py").write_text((MODULE_DIR / "target_binding_worker.py").read_text())
    (tmp_path / "candidate.py").write_text(
        f'import {module} as js\ndef test_parse():\n assert js.loads("[1]") == [1]\n'
    )
    process = subprocess.run(
        [
            "sandbox-exec",
            "-p",
            runner.sandbox(tmp_path),
            str(runner.VENV_PYTHON),
            "-I",
            str(tmp_path / "worker.py"),
            str(tmp_path / "candidate.py"),
        ],
        cwd=tmp_path,
        env={
            "PATH": os.environ["PATH"],
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    records = [
        line.removeprefix("COSMIT_BINDING_JSON=")
        for line in process.stdout.splitlines()
        if line.startswith("COSMIT_BINDING_JSON=")
    ]
    assert records, process.stderr
    result = json.loads(records[-1])
    assert result["pytest_exit_code"] == 0 and result["tests_collected"] == 1
    assert bool(result["target_calls"]) is expect_calls
