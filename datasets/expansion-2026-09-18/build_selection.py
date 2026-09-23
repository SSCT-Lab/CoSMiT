"""Prepare an expansion selection from existing DLLens outputs; never execute them."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "0f617e92c34d60bfdd3bc06d80c17d938879ed9c"
PAIRS = [
    ("add", "torch.add", "tf.add"),
    ("subtract", "torch.sub", "tf.subtract"),
    ("multiply", "torch.mul", "tf.multiply"),
    ("divide", "torch.div", "tf.divide"),
    ("maximum", "torch.maximum", "tf.maximum"),
    ("minimum", "torch.minimum", "tf.minimum"),
    ("power", "torch.pow", "tf.math.pow"),
    ("atan2", "torch.atan2", "tf.atan2"),
    ("reshape", "torch.reshape", "tf.reshape"),
    ("transpose", "torch.transpose", "tf.transpose"),
    ("squeeze", "torch.squeeze", "tf.squeeze"),
    ("expand_dims", "torch.unsqueeze", "tf.expand_dims"),
    ("concat", "torch.concat", "tf.concat"),
    ("stack", "torch.stack", "tf.stack"),
    ("clip", "torch.clip", "tf.clip_by_value"),
]
ALIASES = {
    "sub": "subtract", "mul": "multiply", "div": "divide", "pow": "power",
    "unsqueeze": "expand_dims", "concatenate": "concat", "cat": "concat",
    "clamp": "clip", "clip_by_value": "clip", "permute": "transpose",
}
REFERENCES = {
    "add": "broadcasted scalar a+b", "subtract": "broadcasted scalar a-b",
    "multiply": "broadcasted scalar a*b", "divide": "broadcasted scalar a/b",
    "maximum": "broadcasted scalar max(a,b)", "minimum": "broadcasted scalar min(a,b)",
    "power": "broadcasted scalar math.pow(a,b)", "atan2": "broadcasted scalar math.atan2(first,second)",
    "reshape": "preserve row-major flattened sequence; derive shape from element count and at most one -1",
    "transpose": "derive output shape and index permutation from source dim0/dim1 or perm, including source defaults",
    "squeeze": "remove axes allowed by SOURCE signature; PT nonunit explicit dim is identity; TF explicit axes must be unit",
    "expand_dims": "insert one unit axis; preserve original index order",
    "concat": "sum sizes on selected axis; concatenate index ranges in list order",
    "stack": "insert list-length axis; map each output slice to corresponding input tensor",
    "clip": "scalar min(max(x,lower),upper); source-specific optional-bound rules checked separately",
}
STRUCTURES = {
    "binary": ["same shape [2,3] with asymmetric values", "scalar [] with tensor [2,3]", "[2,1] with [1,3]", "[1,2,1] with [3,1,4]"],
    "reshape": ["[2,3] to [3,2]", "[2,3,4] to [4,6]", "[2,3] to [-1]", "[2,3,4] to [2,-1,2]"],
    "transpose": ["non-square rank-2 axis swap", "rank-3 nontrivial permutation/swap", "equivalent negative axes where source allows", "PT same-axis identity; TF perm=None default reversal"],
    "squeeze": ["leading unit axis [1,2,3]", "interior unit axis [2,1,3]", "multiple unit axes [1,2,1,3]", "PT explicit nonunit axis identity; TF legal unit-axis list/all-axis default"],
    "expand_dims": ["rank-0 scalar insertion", "rank-1 beginning/end insertion", "rank-2 interior insertion", "rank-3 negative legal insertion axis"],
    "concat": ["two [1,3] tensors axis 0", "[2,1] and [2,2] axis 1", "three rank-3 tensors with different concatenated lengths", "equivalent negative axis with unequal concatenated lengths"],
    "stack": ["two rank-0 tensors", "two [3] tensors axis 0", "three [2,3] tensors interior axis", "three rank-3 tensors negative legal axis"],
    "clip": ["scalar input and scalar tensor bounds", "[2,3] with ordered scalar tensor bounds", "[1,2,3] with equal scalar tensor bounds", "PT one-sided None bound; TF ordered scalar bounds at input endpoints"],
}
PATTERNS = ["zero/equality landmarks within domain", "positive landmarks", "negative or lower-domain landmarks", "asymmetric boundary-adjacent landmarks", "seeded finite pattern A", "seeded finite pattern B", "seeded finite pattern C", "seeded finite pattern D"]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def calls(code):
    return sorted({ast.unparse(n.func) for n in ast.walk(ast.parse(code)) if isinstance(n, ast.Call)})


def profile(family):
    binary = family in {p[0] for p in PAIRS[:8]}
    constraints = ["CPU, dense finite real tensors; input rank <= 3, output rank <= 4; <= 256 elements per tensor",
                   "same dtype across tensor operands; float32 and float64 evaluated separately",
                   "source-valid inputs only; source runtime/signature errors retained separately",
                   "no NaN/Inf, complex, sparse, gradients, devices or implicit mixed-dtype promotion in this batch"]
    if binary:
        constraints += ["broadcast-compatible input shapes; values in [-4,4]"]
    if family == "divide":
        constraints += ["abs(denominator) >= 0.25; retain both signs"]
    if family == "power":
        constraints += ["base in [0.25,4], exponent in [-3,3]; positive base only for this batch"]
    if family == "atan2":
        constraints += ["exclude simultaneous zero operands and sign-of-zero assertions in this first domain"]
    if family == "squeeze":
        constraints += ["do not impose a common PT/TF explicit-axis domain; source None handling requires qualification"]
    if family == "reshape":
        constraints += ["contiguous constructed inputs only; no alias/view/storage-preservation claim"]
    if family == "clip":
        constraints += ["both finite bounds ordered when present; optional None tested only if source accepts it; no both-None inputs"]
    return {
        "family": family, "status": "proposed-not-executed-not-source-qualified",
        "reference_design": REFERENCES[family], "constraints": constraints,
        "structural_strata": STRUCTURES["binary" if binary else family],
        "value_patterns_per_stratum": PATTERNS, "planned_inputs_per_candidate": 64,
        "allocation": "2 dtypes x 4 source-specific structural strata x 8 value patterns",
        "deduplication": "require 64 distinct serialized inputs; deterministic refill within same source-valid stratum if landmarks coincide",
        "repetitions": 3, "seed": 20260918,
        "clauses": ["source-reference-validity", "value", "operation-derived-shape", "dtype", "actual-target-operation-binding"],
        "tolerance_proposal": {"float32": {"atol": 1e-6, "rtol": 1e-5}, "float64": {"atol": 1e-12, "rtol": 1e-12}},
        "exact_value_families": ["reshape", "transpose", "squeeze", "expand_dims", "concat", "stack"],
        "freeze_gate": "verify source specification and source-only numerical reference before finalizing inputs/tolerance; never tune to target outcomes",
    }


def build(checkout, out):
    assert subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip() == COMMIT
    if (out / "manifest.json").exists():
        raise FileExistsError("Use a fresh directory; do not overwrite an existing selection")
    out.mkdir(parents=True, exist_ok=True)
    old = {}
    baseline_hashes = {}
    for group in ("discovery", "unseen"):
        path = ROOT / "research-data/2026-09-17" / group / "cases.json"
        baseline_hashes[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
        for c in json.loads(path.read_text(encoding="utf-8")):
            old[c["upstream_path"]] = c["id"]
    selected, selected_paths = [], set()
    for family, pt, tf in PAIRS:
        for fw, api in (("pytorch", pt), ("tensorflow", tf)):
            other = "tensorflow" if fw == "pytorch" else "pytorch"
            rel = f"data/working_dir/rq1/dllens/{fw}/counterparts/{api}.json"
            assert rel not in old
            raw = (checkout / rel).read_bytes()
            committed = subprocess.check_output(["git", "-C", str(checkout), "show", COMMIT + ":" + rel])
            assert raw.replace(b"\r\n", b"\n") == committed.replace(b"\r\n", b"\n")
            d = json.loads(raw)
            cid = f"E{len(selected)+1:03d}"
            dest = out / "local-sources" / cid
            dest.mkdir(parents=True)
            (dest / "upstream.json").write_bytes(raw)
            sides = {}
            for side, framework in (("source", fw), ("target", other)):
                code = d["counterparts"][framework]
                ast.parse(code)
                file = dest / (side + ".py")
                file.write_bytes(code.encode("utf-8"))
                sides[side] = {"framework": framework, "entry": framework + "_call", "code_path": file.relative_to(out).as_posix(),
                               "code_sha256": sha(code.encode()), "syntactic_calls": calls(code), "runtime_binding_status": "not-executed"}
            requirements = ["two-framework isolated execution with preserved argument names", "source reference, shaped observation and actual target-call logging"]
            if family in {p[0] for p in PAIRS[:8]}:
                requirements += ["two typed tensor arguments and broadcasting reference"]
            if family in {"concat", "stack"}:
                requirements += ["recursive tensor-list arguments; derive list-length/axis output shape"]
            if family in {"reshape", "transpose", "squeeze", "expand_dims", "clip"}:
                requirements += ["typed literal/list/None arguments; source-specific default handling"]
            if any(not call.startswith(("torch.", "tf.")) and "." in call for call in sides["target"]["syntactic_calls"]):
                requirements += ["resolve Tensor instance method binding; cannot infer no target call from absence of torch.* AST names"]
            notes = []
            if family == "transpose" and fw == "tensorflow":
                notes += ["Source exposes perm=None; include its default semantics in source qualification, do not silently restrict to explicit perm after seeing target code."]
            if family == "squeeze":
                notes += ["PT and TF explicit nonunit-axis semantics differ. Include only source-valid cases; qualify callable's None handling before registering defaults."]
            if family == "clip":
                notes += ["Inspect actual bound argument types; scalar tensors and None are not interchangeable. Preserve original target code, including its composite operations."]
            if family == "reshape" and fw == "tensorflow":
                notes += ["Target calls tensor.view; record torch.Tensor.view. Contiguous constructed domain does not test noncontiguous views."]
            selected.append({"case_id": cid, "family": family, "direction": fw + "-to-" + other,
                             "source_api": api, "source_signature": d["function_name"], "argument_names": d["inputs"],
                             **sides, "upstream_commit": COMMIT, "upstream_path": rel,
                             "upstream_url": f"https://github.com/maybeLee/DLLens/blob/{COMMIT}/{rel}",
                             "upstream_worktree_sha256": sha(raw), "upstream_git_blob_sha256": sha(committed),
                             "original_sample_inputs": len(d.get("sample_inputs", [])),
                             "input_profile": "input-design.json#" + family,
                             "required_adaptations": requirements, "review_notes": notes,
                             "selection_reason": "one canonical public counterpart per family and direction; no runtime outcome selection",
                             "status": "selected-source-validation-pending", "execution_count": 0,
                             "exposure": "new-to-2026-09-17-campaign; code-reviewed expansion-development; not unseen holdout",
                             "prior_research_exposure": "not audited; some families occurred in older development work",
                             "formal_gold": False})
            selected_paths.add(rel)
    assert len(selected) == 30 and len({(c["family"], c["direction"]) for c in selected}) == 30
    assert len({(c["source"]["code_sha256"], c["target"]["code_sha256"]) for c in selected}) == 30
    inventory = []
    families = {p[0] for p in PAIRS}
    for fw in ("pytorch", "tensorflow"):
        for path in sorted((checkout / f"data/working_dir/rq1/dllens/{fw}/counterparts").glob("*.json")):
            rel = path.relative_to(checkout).as_posix()
            leaf = path.stem.split(".")[-1]
            family = ALIASES.get(leaf, leaf)
            status = ("selected" if rel in selected_paths else "already-in-existing-campaign" if rel in old else
                      "same-name-family-variant-deferred" if family in families else "outside-this-batch-not-eligibility-reviewed")
            inventory.append({"upstream_path": rel, "framework": fw, "api": path.stem, "status": status,
                              "existing_case_id": old.get(rel), "note": "same-name variants may include sparse/Keras semantics; this is not proof of equivalence" if status == "same-name-family-variant-deferred" else None})
    save(out / "candidates.json", selected)
    save(out / "input-design.json", {p[0]: profile(p[0]) for p in PAIRS})
    save(out / "selection-inventory.json", inventory)
    save(out / "protocol-draft.json", {
        "status": "selection-ready; execution-protocol-not-yet-frozen", "partition": "expansion-development",
        "baseline": "research-data/2026-09-17", "candidates": 30, "families": 15,
        "budget_proposal": {"inputs_per_case": 64, "repeats": 3, "pairs_total": 5760, "model_requests_if_all_five_components_run": 150},
        "actual_runs": 0, "model_calls": 0,
        "required_gates": ["fixed-version source specifications", "typed multiargument/list adapters", "source-only qualification and reference checks",
                           "freeze inputs/tolerances and environment before target execution", "common input pool for all dynamic comparators",
                           "retain source-invalid/target-error/unbound/unsupported outcomes", "audit every reported counterexample", "model pilot before batch requests"],
        "comparison": "same input and observation budget; any revised model/prompt/environment version reported separately",
        "preservation": "do not modify public counterparts; do not replace failed candidates after observing outcomes",
        "not_an_executable_packet": "existing v3 workers only register unary/matrix domains; new domains and adapters must be implemented first",
    })
    lines = ["# 第一批实验扩充清单", "", "30 条公开 counterpart，15 个家族，两个迁移方向。只完成代码检查与选择，未执行框架或模型。", "",
             "| ID | 家族 | 源 API | 方向 | 参数 |", "| --- | --- | --- | --- | --- |"]
    for c in selected:
        lines.append(f"| {c['case_id']} | {c['family']} | {c['source_api']} | {c['direction']} | {', '.join(c['argument_names'])} |")
    lines += ["", "每条代码位置、哈希、调用、适配要求和边界说明见 candidates.json；输入域与 64 输入分层设计见 input-design.json。",
              "", "当前名单以新增实验覆盖为目的；并未根据执行失败筛选。Tensor 方法、别名和包装层另列在 selection-inventory.json，不计作新增家族。"]
    (out / "SELECTION.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    save(out / "manifest.json", {"date": "2026-09-18", "purpose": "expand existing completed research-data campaign, not revive prior pilot dataset",
                                "selected": 30, "families": 15, "directions": dict(Counter(c["direction"] for c in selected)),
                                "inventory_total": len(inventory), "inventory_counts": dict(Counter(i["status"] for i in inventory)),
                                "overlap_with_existing_81": 0, "upstream_commit": COMMIT, "previous_case_file_hashes": baseline_hashes,
                                "build_script_sha256": sha(Path(__file__).read_bytes()), "framework_executions": 0, "model_calls": 0,
                                "status": "selection-and-input-design-complete; qualification-and-execution-pending"})
    save(out / "SHA256.json", {p.relative_to(out).as_posix(): sha(p.read_bytes()) for p in sorted(out.rglob("*"))
                               if p.is_file() and p.name != "SHA256.json" and "__pycache__" not in p.parts})
    print(json.dumps({"selected": len(selected), "families": len(families), "inventory": len(inventory), "executions": 0}, indent=2))


def verify(out):
    data = json.loads((out / "candidates.json").read_text(encoding="utf-8"))
    assert len(data) == 30
    for c in data:
        for side in ("source", "target"):
            path = out / c[side]["code_path"]
            assert sha(path.read_bytes()) == c[side]["code_sha256"]
            tree = ast.parse(path.read_text(encoding="utf-8"))
            fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == c[side]["entry"])
            assert [a.arg for a in fn.args.args] == c["argument_names"]
    for rel, expected in json.loads((out / "SHA256.json").read_text(encoding="utf-8")).items():
        assert sha((out / rel).read_bytes()) == expected, rel
    print("Verified: 30 cases, 60 unchanged function bodies, argument signatures, and all manifest hashes.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", type=Path)
    p.add_argument("--output", type=Path, default=Path(__file__).parent)
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    if args.verify:
        verify(args.output)
    else:
        build(args.checkout, args.output)
