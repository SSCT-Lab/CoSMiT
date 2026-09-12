"""Perform source replay and clause checks for KATRER reproduction candidates."""

from __future__ import annotations

import argparse
import ast
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy
import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "benchmark/public_systems/katrer-reproduction-inputs.yaml"
DEFAULT_CANDIDATES = ROOT / "benchmark/public_systems/katrer-reproduction-results.json"
DEFAULT_OUTPUT = ROOT / "benchmark/public_systems/katrer-property-check-results-v0.2.json"


def conservative_test_tree(code: str) -> tuple[ast.Module | None, str]:
    """Recognize a narrow straight-line test subset; this is NOT a semantic proof.

    Branches, helper indirection, shadowed imports and decorators require dynamic
    analysis. Refusing a structural signal means unknown, not invalid migration.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return None, f"syntax error: {error.msg}"
    tests = [
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
    ]
    if not tests:
        return None, "no recognizable test functions"
    aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".")[0]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name == "*":
                    return None, "wildcard import unresolved"
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
        elif not isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            return None, "top-level residual code"
    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.If,
                ast.For,
                ast.While,
                ast.Try,
                ast.Raise,
                ast.Return,
                ast.Lambda,
                ast.AsyncFunctionDef,
                ast.ListComp,
                ast.GeneratorExp,
                ast.IfExp,
            ),
        ):
            return None, "control flow requires dynamic analysis"
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.decorator_list:
            return None, "decorated tests require collection/execution"
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_"):
            return None, "helper function requires dynamic analysis"
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in aliases:
            return None, "import alias rebound"
        if isinstance(node, ast.arg) and node.arg in aliases:
            return None, "import alias shadowed"
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node not in tree.body:
            return None, "nested import unresolved"

    # Canonicalize module aliases without executing imports.
    class CanonicalNames(ast.NodeTransformer):
        def visit_Name(self, node: ast.Name) -> ast.AST:
            if isinstance(node.ctx, ast.Load) and node.id in aliases:
                return ast.copy_location(ast.parse(aliases[node.id], mode="eval").body, node)
            return node

    return CanonicalNames().visit(tree), "straight-line AST signal only"


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def literal_int(node: ast.AST | None) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = literal_int(node.operand)
        return -value if value is not None else None
    return None


def argument_int(call: ast.Call, position: int, keyword: str) -> int | None:
    for item in call.keywords:
        if item.arg == keyword:
            return literal_int(item.value)
    if len(call.args) > position:
        return literal_int(call.args[position])
    return None


def exception_clause_preserved(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.With):
            continue
        catches_value_error = any(
            isinstance(item.context_expr, ast.Call)
            and call_name(item.context_expr.func) == "pytest.raises"
            and item.context_expr.args
            and call_name(item.context_expr.args[0]) == "ValueError"
            for item in node.items
        )
        if not catches_value_error:
            continue
        for child in ast.walk(ast.Module(body=node.body, type_ignores=[])):
            if (
                isinstance(child, ast.Call)
                and call_name(child.func) == "cupy.fft.fft"
                and argument_int(child, 1, "n") == 0
            ):
                return True
    return False


def fft_boundary_clause_preserved(tree: ast.AST) -> bool:
    observed: list[tuple[str, int | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = call_name(node.func)
            if name in {"cupy.fft.irfft", "cupy.fft.hfft"}:
                observed.append((name.split(".")[-1], argument_int(node, 1, "n")))
    required = [("irfft", 1), ("hfft", 1), ("irfft", 10)]
    return all(required.count(item) <= observed.count(item) for item in set(required))


def squeeze_clause_preserved(tree: ast.AST) -> bool:
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    squeeze_count = sum(call_name(node.func) == "cupy.squeeze" for node in calls)
    reshape_count = sum(call_name(node.func) == "cupy.reshape" for node in calls)
    assertions = [node.test for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    zero_dim_check = any(
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Attribute)
        and node.left.attr == "ndim"
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Eq)
        and any(literal_int(comparator) == 0 for comparator in node.comparators)
        for node in assertions
    )
    ndarray_type_check = any(
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Is)
        and isinstance(node.left, ast.Call)
        and call_name(node.left.func) == "type"
        and len(node.comparators) == 1
        and call_name(node.comparators[0]) == "cupy.ndarray"
        for node in assertions
    )
    value_assertions = sum(
        call_name(node.func) == "cupy.testing.assert_array_equal" for node in calls
    )
    return (
        squeeze_count >= 4
        and reshape_count >= 3
        and zero_dim_check
        and ndarray_type_check
        and value_assertions >= 4
    )


def candidate_clause_check(case_id: str, code: str) -> tuple[bool, str]:
    tree, detail = conservative_test_tree(code)
    if tree is None:
        return False, detail
    checks = {
        "KATRER-NC-001": exception_clause_preserved,
        "KATRER-NC-002": fft_boundary_clause_preserved,
        "KATRER-NC-003": squeeze_clause_preserved,
    }
    if case_id not in checks:
        return False, "no clause checker registered"
    passed = checks[case_id](tree)
    return (
        passed,
        "structural clause signal only; behavior unverified"
        if passed
        else "signal absent or unresolved",
    )


def target_static_evidence(case_id: str, root: Path) -> tuple[bool, list[str]]:
    evidence: list[str] = []
    if case_id == "KATRER-NC-001":
        path = root / "tmp/cupy-13.5.1/cupy/fft/_fft.py"
        text = path.read_text(encoding="utf-8")
        passed = "if n < 1:" in text and "Invalid number of FFT data points" in text
        if passed:
            evidence.append(f"{path.relative_to(root)}:105")
        return passed, evidence
    if case_id == "KATRER-NC-002":
        path = root / "tmp/cupy-13.5.1/cupy/fft/_fft.py"
        text = path.read_text(encoding="utf-8")
        passed = "def irfft(" in text and "def hfft(" in text
        if passed:
            evidence.extend([f"{path.relative_to(root)}:843", f"{path.relative_to(root)}:1003"])
        return passed, evidence
    if case_id == "KATRER-NC-003":
        squeeze = root / "tmp/cupy-13.5.1/cupy/_manipulation/dims.py"
        reshape = root / "tmp/cupy-13.5.1/cupy/_manipulation/shape.py"
        passed = "def squeeze(" in squeeze.read_text(
            encoding="utf-8"
        ) and "def reshape(" in reshape.read_text(encoding="utf-8")
        if passed:
            evidence.extend([f"{squeeze.relative_to(root)}:151", f"{reshape.relative_to(root)}:23"])
        return passed, evidence
    return False, evidence


def replay_source(path: Path, timeout: int) -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "status": "passed" if process.returncode == 0 else "failed",
        "exit_code": process.returncode,
        "stdout": process.stdout[-4000:],
        "stderr": process.stderr[-4000:],
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    candidate_data = json.loads(args.candidates.read_text(encoding="utf-8"))
    records_by_id = {item["case_id"]: item for item in candidate_data["records"]}
    checks = []
    for case in manifest["cases"]:
        case_id = case["case_id"]
        candidate = records_by_id[case_id]
        source_replay = replay_source(ROOT / case["source_test_path"], args.timeout)
        clause_preserved, clause_detail = candidate_clause_check(
            case_id, candidate["candidate_code"]
        )
        target_evidence, target_evidence_paths = target_static_evidence(case_id, ROOT)
        # Neither passing source replay nor target-source keyword matches prove
        # behavior of the migrated test. No static positive certification.
        status = "undetermined"
        check = {
            "case_id": case_id,
            "source_property": case["source_property"],
            "source_replay": source_replay,
            "candidate_clause_signal_observed": clause_preserved,
            "candidate_clause_detail": clause_detail,
            "target_static_evidence_observed": target_evidence,
            "target_static_evidence": target_evidence_paths,
            "llm_consistency_judgement": candidate["llm_consistency_judgement"],
            "certificate_status": status,
            "dynamic_target_execution": "unavailable-target-runtime",
        }
        checks.append(check)

    result = {
        "schema_version": "0.2",
        "dataset": "katrer-reproduction-property-check",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": numpy.__version__,
            "expected_numpy": manifest["upstream"]["source_library"]["version"],
            "source_version_matches": numpy.__version__
            == manifest["upstream"]["source_library"]["version"],
            "target_runtime": "cupy unavailable",
        },
        "scope_note": "Static source support is not a substitute for executing the target candidate on CuPy 13.5.1.",
        "checks": checks,
    }
    write_json(args.output, result)
    print(f"checked {len(checks)} candidate(s); wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
