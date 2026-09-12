"""Export development cases without labels or probes for a human reviewer.

Constant specialization exposes each registered program without the REF/MUT or
adapted selector. The key is written outside the packet directory. This is NOT
independent review; reviewer identity and judgments remain empty.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


class Specialize(ast.NodeTransformer):
    def __init__(self, constants: dict[str, Any]) -> None:
        self.constants = constants

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if isinstance(node.ctx, ast.Load) and node.id in self.constants:
            return ast.copy_location(ast.Constant(self.constants[node.id]), node)
        return node

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        node = self.generic_visit(node)
        if (
            isinstance(node.left, ast.Constant)
            and len(node.ops) == 1
            and isinstance(node.ops[0], ast.Eq)
            and isinstance(node.comparators[0], ast.Constant)
        ):
            return ast.copy_location(
                ast.Constant(node.left.value == node.comparators[0].value), node
            )
        return node

    def visit_If(self, node: ast.If) -> ast.AST | list[ast.stmt]:
        node = self.generic_visit(node)
        if isinstance(node.test, ast.Constant) and isinstance(node.test.value, bool):
            return node.body if node.test.value else node.orelse
        return node

    def visit_IfExp(self, node: ast.IfExp) -> ast.AST:
        node = self.generic_visit(node)
        if isinstance(node.test, ast.Constant) and isinstance(node.test.value, bool):
            return node.body if node.test.value else node.orelse
        return node


def program(source: str, name: str, family: str, adapted: bool | None) -> str:
    tree = ast.parse(source)
    selected = copy.deepcopy(
        next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    )
    constants: dict[str, Any] = {"family": family}
    if adapted is not None:
        constants["adapted"] = adapted
    selected.args.args = [arg for arg in selected.args.args if arg.arg not in constants]
    selected.name = "source_operation" if name == "source" else "candidate_operation"
    module = Specialize(constants).visit(ast.Module(body=[selected], type_ignores=[]))
    ast.fix_missing_locations(module)
    code = ast.unparse(module) + "\n"
    compile(code, "<review-program>", "exec")
    return code


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("review"))
    args = parser.parse_args()
    manifest = json.loads((args.run_directory / "manifest.json").read_text())
    code = Path(__file__).with_name("kernels.py").read_text()
    root = Path(__file__).resolve().parents[2]
    properties = {}
    evidence = {}
    for relative in [
        "benchmark/pilot/properties.yaml",
        "benchmark/pilot/properties-seed-v0.2.yaml",
    ]:
        for record in yaml.safe_load((root / relative).read_text())["records"]:
            properties[record["property_id"]] = record
    for relative in ["benchmark/pilot/evidence.yaml", "benchmark/feasibility/evidence.yaml"]:
        for record in yaml.safe_load((root / relative).read_text())["records"]:
            evidence[record["evidence_id"]] = record
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output / "packet.json").exists():
        parser.error("review packet already exists; select a new --output")
    records, key = [], []
    for subject in manifest["subjects"]:
        for candidate in subject["candidates"]:
            blind_id = hashlib.sha256(("review-v1:" + candidate["id"]).encode()).hexdigest()[:12]
            record = {
                "blind_id": blind_id,
                "property_id": subject["property_id"],
                "oracle": subject["oracle"],
                "atol": subject["atol"],
                "rtol": subject["rtol"],
                "valid_shapes": subject["shapes"],
                "domain": subject["domain"],
                "scope_relation": subject["scope_relation"],
                "source_code": program(code, "source", subject["family"], None),
                "candidate_code": program(
                    code,
                    "target",
                    subject["family"],
                    candidate["origin"] == "evidence-derived-reference",
                ),
                "reviewer": None,
                "property_boundary_review": None,
                "candidate_relation_review": None,
                "evidence_state_review": None,
                "source_evidence": [
                    {key: evidence[eid][key] for key in ["evidence_id", "url", "role"]}
                    for eid in properties[subject["property_id"]]["property"]["provenance"]
                    if eid in evidence and "url" in evidence[eid]
                ],
                "reviewer_evidence_links": [],
                "review_minutes": None,
                "notes": None,
            }
            records.append(record)
            key.append(
                {
                    "blind_id": blind_id,
                    "candidate_id": candidate["id"],
                    "origin": candidate["origin"],
                }
            )
    records.sort(key=lambda r: r["blind_id"])
    helper = next(
        n
        for n in ast.parse(code).body
        if isinstance(n, ast.FunctionDef) and n.name == "observation"
    )
    payload = {
        "status": "awaiting-human-review",
        "environment": manifest["environment"],
        "scope": "development-only; not a held-out test",
        "instructions": "Review fixed source evidence and code before judging. Do not consult system traces, candidate origins or the key. Reference provenance alone does not establish universal validity.",
        "observation_helper": ast.unparse(helper),
        "required_imports": [
            "numpy as np",
            "torch",
            "tensorflow as tf",
            "Observation from cosmit.engine.certification",
        ],
        "records": records,
    }
    (args.output / "packet.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    args.output.with_name(args.output.name + "-key.json").write_text(
        json.dumps(key, indent=2) + "\n"
    )
    print(f"prepared {len(records)} blind development records; all reviewer fields empty")


if __name__ == "__main__":
    main()
