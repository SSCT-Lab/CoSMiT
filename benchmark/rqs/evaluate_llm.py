"""Execute model-generated DATA probes through the same trusted development kernels."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import tensorflow as tf
import torch
from subjects import subjects

from cosmit.engine.certification import certify
from cosmit.engine.mapping_ir import normalize_candidate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("llm_directory", type=Path)
    parser.add_argument("packet", type=Path)
    parser.add_argument("review_key", type=Path)
    args = parser.parse_args()
    torch.set_num_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    manifest = json.loads((args.run_directory / "manifest.json").read_text())
    if (
        torch.__version__ != manifest["environment"]["torch"]
        or tf.__version__ != manifest["environment"]["tensorflow"]
    ):
        raise RuntimeError("baseline runtime versions differ")
    prior = [
        json.loads(s) for s in (args.run_directory / "campaigns.jsonl").read_text().splitlines()
    ]
    records = json.loads(args.packet.read_text())["records"]
    mapping = json.loads(args.review_key.read_text())
    blind_by_id = {r["candidate_id"]: r["blind_id"] for r in mapping}
    records_by_blind = {r["blind_id"]: r for r in records}
    output = []
    for subject in subjects():
        probe_path = args.llm_directory / ("probes-" + subject.prop.property_id + ".json")
        response = json.loads(probe_path.read_text()) if probe_path.exists() else {}
        for candidate in subject.candidates:
            blind_id = blind_by_id[candidate.candidate_id]
            judge_path = args.llm_directory / ("judge-" + blind_id + ".json")
            judge = json.loads(judge_path.read_text()) if judge_path.exists() else {}
            row = {
                "candidate_id": candidate.candidate_id,
                "direct_judgment_status": judge.get("status", "not-run"),
                "direct_judgment": judge.get("parsed"),
                "probe_status": response.get("status", "not-run"),
                "scope": "one fixed LLM response; not ten independent seeds",
                "mapping_ir": asdict(
                    normalize_candidate(
                        "import tensorflow as tf\n" + records_by_blind[blind_id]["candidate_code"],
                        "tensorflow",
                    )
                ),
            }
            if response.get("status") == "completed":
                data = response["parsed"]["probes"]
                sanitized = []
                for probe in data:
                    try:
                        json.dumps(probe, allow_nan=False)
                        sanitized.append(probe)
                    except ValueError:
                        sanitized.append({"invalid-data": "non-finite JSON value"})
                row["probe_execution"] = certify(
                    subject.prop, candidate, sanitized, manifest["pair_execution_budget"]
                )
            witnesses = [
                r
                for r in prior
                if r["candidate_id"] == candidate.candidate_id and r["evidence_state"] == "refuted"
            ]
            if judge.get("status") == "completed":
                row["judgment_conflicts_with_recorded_counterexample"] = (
                    bool(witnesses) and judge["parsed"]["verdict"] == "consistent"
                )
            output.append(row)
    target = args.llm_directory / "evaluation.json"
    if target.exists():
        parser.error("evaluation exists; do not overwrite a previous evaluation snapshot")
    target.write_text(
        json.dumps({"independent_gold": False, "records": output}, indent=2, allow_nan=False) + "\n"
    )
    print(
        f"evaluated {len(output)} expected candidates; missing/failed model outputs kept separate"
    )


if __name__ == "__main__":
    main()
