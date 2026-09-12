"""Conservative, evidence-preserving intake of candidate Python call structure.

This IR describes syntax, not semantic equivalence or runtime binding. Unknown
control flow and calls remain explicit residual code; they never certify a test.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class CallIR:
    qualified_name: str
    arguments: tuple[str, ...]
    keywords: tuple[tuple[str, str], ...]
    line: int
    category: str


@dataclass(frozen=True)
class MappingIR:
    code_sha256: str
    calls: tuple[CallIR, ...]
    residual_code: tuple[str, ...]
    target_module: str
    evidence_kind: str = "syntax-only"


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else ""
    return ""


def normalize_candidate(code: str, target_module: str) -> MappingIR:
    digest = hashlib.sha256(code.encode()).hexdigest()
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return MappingIR(digest, (), (f"syntax-error:{error.lineno}",), target_module)
    aliases: dict[str, str] = {}
    residual: list[str] = []
    node: ast.AST
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name == "*":
                    residual.append(f"wildcard-import:{node.lineno}")
                else:
                    aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    shadowed = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in aliases
    }
    shadowed.update(
        node.arg for node in ast.walk(tree) if isinstance(node, ast.arg) and node.arg in aliases
    )
    for alias_name in sorted(shadowed):
        residual.append(f"shadowed-import:{alias_name}")
        aliases.pop(alias_name)
    calls = []
    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.If,
                ast.For,
                ast.While,
                ast.Try,
                ast.With,
                ast.IfExp,
                ast.Lambda,
                ast.ListComp,
                ast.GeneratorExp,
            ),
        ):
            residual.append(f"control-flow:{node.lineno}:{ast.unparse(node)}")
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node not in tree.body:
            residual.append(f"nested-import:{node.lineno}")
        if not isinstance(node, ast.Call):
            continue
        name = dotted(node.func)
        root, _, suffix = name.partition(".")
        qualified = aliases.get(root, "")
        if qualified and suffix:
            qualified += "." + suffix
        if not qualified or qualified.split(".")[0] != target_module:
            residual.append(f"unresolved-call:{node.lineno}:{ast.unparse(node)}")
            continue
        operation = qualified.split(".")[-1]
        category = {
            "cast": "input-dtype",
            "transpose": "axis-permutation",
            "reshape": "shape-transform",
            "squeeze": "shape-transform",
            "assert_near": "oracle",
            "assert_close": "oracle",
        }.get(operation, "operation")
        calls.append(
            CallIR(
                qualified,
                tuple(ast.unparse(arg) for arg in node.args),
                tuple((kw.arg or "**", ast.unparse(kw.value)) for kw in node.keywords),
                node.lineno,
                category,
            )
        )
    return MappingIR(digest, tuple(calls), tuple(dict.fromkeys(residual)), target_module)
