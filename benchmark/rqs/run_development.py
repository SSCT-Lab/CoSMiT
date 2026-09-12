"""Execute RQ development campaigns; not a held-out or independently gold study.

Run: PYTHONPATH=src python3 benchmark/rqs/run_development.py --seeds 10 --budget 12
Only trusted kernels registered in subjects.py are executed. No model calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Fixed CPU execution; do not expose model credentials to subprocesses or results.
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
import tensorflow as tf
import torch
from subjects import make_probe, probes, shrink, subjects

from cosmit.engine.certification import certify, check_conditions, minimize

ROOT = Path(__file__).resolve().parents[2]


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--budget", type=int, default=12)
    parser.add_argument("--output-root", type=Path, default=ROOT / "artifacts/research-rqs")
    args = parser.parse_args()
    if args.seeds < 1 or args.budget < 3:
        parser.error("seeds >= 1 and budget >= 3 required")
    if torch.__version__.split("+")[0] != "2.9.1" or tf.__version__ != "2.20.0":
        raise RuntimeError("frozen subject versions require torch 2.9.1 / TensorFlow 2.20.0")
    torch.set_num_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    run_dir = args.output_root / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir.mkdir(parents=True, exist_ok=False)
    all_subjects = subjects()
    source_paths = [
        Path(__file__),
        Path(__file__).with_name("kernels.py"),
        Path(__file__).with_name("subjects.py"),
        ROOT / "src/cosmit/engine/certification.py",
        ROOT / "benchmark/pilot/properties-seed-v0.2.yaml",
        ROOT / "benchmark/pilot/properties.yaml",
    ]
    manifest = {
        "run_id": run_dir.name,
        "scope": "development-only controlled executable fixtures",
        "independent_gold": False,
        "holdout_opened": False,
        "model_calls": 0,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "tensorflow": tf.__version__,
            "device": "CPU",
            "threads": 1,
        },
        "seeds": list(range(args.seeds)),
        "pair_execution_budget": args.budget,
        "confirmation_pairs": 2,
        "minimization_budget_separate": 24,
        "policies": ["original", "random", "boundary", "clause-aware"],
        "original_policy_note": "historical hand-selected feasibility witness; NOT official original regression",
        "source_hashes": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in source_paths
        },
        "subjects": [
            {
                "property_id": s.prop.property_id,
                "family": s.family,
                "oracle": s.prop.oracle,
                "clause": s.prop.clause_id,
                "atol": s.prop.atol,
                "rtol": s.prop.rtol,
                "shapes": s.shapes,
                "historical_input": s.original,
                "scope_relation": "parameterized development extension; not a frozen gold label",
                "domain": {
                    "dtype": s.original["dtype"],
                    "finite": True,
                    "abs_input_bound": 4096 if s.original["dtype"].startswith("int") else 10,
                    "integral_values_required": s.original["dtype"].startswith("int"),
                    "labels": "CE only: integral shape [N,L], 0 <= label < C",
                },
                "candidates": [
                    {"id": c.candidate_id, "origin": c.origin, "code_sha256": c.code_sha256}
                    for c in s.candidates
                ],
            }
            for s in all_subjects
        ],
        "excluded_existing_property": {
            "CCP-025": "stateful observation/mapping intake not implemented"
        },
        "missing_comparators": [
            "official-original-input",
            "LLM judgement",
            "LLM probes",
            "official ONNX mappings",
            "public-system-output execution in this engine",
        ],
    }
    write_json(run_dir / "manifest.json", manifest)
    jobs = [
        (s, c, policy, seed)
        for s in all_subjects
        for c in s.candidates
        for policy in manifest["policies"]
        for seed in manifest["seeds"]
    ]
    random.Random(20260909).shuffle(jobs)
    results = []
    started = time.perf_counter()
    for index, (subject, candidate, policy, seed) in enumerate(jobs):
        start_generation = time.perf_counter()
        inputs = probes(subject, policy, seed, args.budget)
        generation_seconds = time.perf_counter() - start_generation
        record = certify(subject.prop, candidate, inputs, args.budget)
        record.update(
            policy=policy,
            seed=seed,
            family=subject.family,
            proposal_seconds=generation_seconds,
            proposal_count=len(inputs),
        )
        results.append(record)
        # Append each finished campaign for crash recovery, with no secret data.
        with (run_dir / "campaigns.jsonl").open("a") as handle:
            handle.write(json.dumps(record, allow_nan=False) + "\n")
        if (index + 1) % 96 == 0:
            print(f"{index + 1}/{len(jobs)} campaigns complete", flush=True)
    reductions = []
    for subject in all_subjects:
        for candidate in subject.candidates:
            successes = [
                r
                for r in results
                if r["candidate_id"] == candidate.candidate_id
                and r["policy"] == "clause-aware"
                and r["witness"] is not None
            ]
            if successes:
                witness = min(successes, key=lambda r: r["seed"])["witness"]
                reduction = minimize(subject.prop, candidate, witness, shrink, 24)
                reductions.append({"candidate_id": candidate.candidate_id, **reduction})
    write_json(run_dir / "minimization.json", reductions)
    refinements = []
    for subject in all_subjects:
        if subject.family not in {"clamp", "squeeze"}:
            continue
        rng = np.random.default_rng(7842)
        seen: set[str] = set()
        samples = []
        while len(samples) < 80:
            shape = subject.shapes[len(samples) % len(subject.shapes)]
            sample = make_probe(subject, rng, shape, "random")
            key = json.dumps(sample, sort_keys=True)
            if key not in seen:
                samples.append(sample)
                seen.add(key)
        conditions = (
            {"selected-axis-size == 1": lambda x: np.asarray(x["values"]).shape[1] == 1}
            if subject.family == "squeeze"
            else {"max(input) <= 999": lambda x: np.max(x["values"]) <= 999}
        )
        for candidate in subject.candidates:
            checked = check_conditions(
                subject.prop, candidate, conditions, samples[:40], samples[40:]
            )
            refinements.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "grammar": list(conditions),
                    "grammar_origin": "manually registered source guard / target literal",
                    "discovery_inputs": samples[:40],
                    "validation_inputs": samples[40:],
                    "results": checked,
                }
            )
    write_json(run_dir / "conditions.json", refinements)
    summaries = []
    for policy in manifest["policies"]:
        for origin in ["researcher-mutant", "evidence-derived-reference"]:
            group = [r for r in results if r["policy"] == policy and r["origin"] == origin]
            summaries.append(
                {
                    "policy": policy,
                    "origin": origin,
                    "campaigns": len(group),
                    "states": dict(Counter(r["evidence_state"] for r in group)),
                    "executions": sum(r["executions"] for r in group),
                    "unique_candidates": len({r["candidate_id"] for r in group}),
                    "note": "seed campaigns are repeated measures, NOT independent samples",
                }
            )
    summary = {
        "manifest": "manifest.json",
        "campaign_count": len(results),
        "results": summaries,
        "elapsed_seconds": time.perf_counter() - started,
        "status": "development results only; no gold precision/recall or superiority claim",
        "minimality": "greedy, bounded, input-grammar-relative",
        "rq3_root_cause_accuracy": None,
        "independent_review_cost": None,
    }
    write_json(run_dir / "summary.json", summary)
    print(json.dumps({"run_directory": str(run_dir), **summary}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
