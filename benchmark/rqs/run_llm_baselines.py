"""Run bounded direct-judgment / JSON-probe baselines on blinded development cases.

Requires explicit --execute. Never executes generated code. Failed calls are
persisted; no automatic retries or replacement of existing response artifacts.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def requests(packet: dict[str, Any]) -> list[dict[str, str]]:
    jobs = []
    seen = set()
    for record in packet["records"]:
        common = {
            k: record[k]
            for k in [
                "property_id",
                "oracle",
                "atol",
                "rtol",
                "valid_shapes",
                "domain",
                "source_code",
            ]
        }
        common["environment"] = packet["environment"]
        common["observation_helper"] = packet["observation_helper"]
        candidate = {**common, "candidate_code": record["candidate_code"]}
        jobs.append(
            {
                "job_id": "judge-" + record["blind_id"],
                "kind": "judgment",
                "blind_id": record["blind_id"],
                "prompt": "Independently judge whether the supplied target program preserves the source oracle throughout the declared domain. Return only JSON with verdict equal to consistent, inconsistent or undetermined, and a short reason. You have no execution results.\n"
                + json.dumps(candidate),
            }
        )
        if record["property_id"] not in seen:
            seen.add(record["property_id"])
            jobs.append(
                {
                    "job_id": "probes-" + record["property_id"],
                    "kind": "probes",
                    "property_id": record["property_id"],
                    "prompt": "Generate at most 12 diverse valid inputs likely to expose errors in cross-library preservation of this source property. You are not given a candidate. Return only JSON with key probes, a list of objects containing values (nested numeric arrays) and dtype. For cross entropy also provide integral labels of shape [N,L] with 0<=label<C. Obey domain constraints; return data, not code.\n"
                    + json.dumps(common),
                }
            )
    return jobs


def parse_answer(content: str) -> dict[str, Any]:
    start, end = content.find("{"), content.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object")
    value = json.loads(content[start : end + 1])
    if not isinstance(value, dict):
        raise TypeError("expected JSON object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.limit < 1 or not 1 <= args.workers <= 4:
        parser.error("positive limit and 1 to 4 workers required")
    packet = json.loads(args.packet.read_text())
    jobs = requests(packet)
    args.output.mkdir(parents=True, exist_ok=True)
    request_path = args.output / "requests.json"
    encoded = json.dumps(jobs, indent=2) + "\n"
    if request_path.exists() and request_path.read_text() != encoded:
        parser.error("frozen requests differ; use a new output directory")
    request_path.write_text(encoded)
    if not args.execute:
        print(f"prepared {len(jobs)} requests; no API calls")
        return
    path = ROOT / "benchmark/public_systems/katrer_reproduction.py"
    spec = importlib.util.spec_from_file_location("rq_llm_transport", path)
    transport = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = transport
    spec.loader.exec_module(transport)
    transport.load_env_file(ROOT / ".env.njusehub")
    endpoint = os.environ.get("NJUSEHUB_BASE_URL", "")
    key = os.environ.get("NJUSEHUB_API_KEY", "")
    if not endpoint or not key:
        parser.error("configured model credentials unavailable")
    config = transport.ModelConfig("DeepSeek-R1", 0.6, 0.95, 1.0, 4096)
    metadata = {
        "model": config.__dict__,
        "checkpoint_verified": False,
        "retry_count": 0,
        "endpoint": endpoint,
        "packet_sha256": hashlib.sha256(args.packet.read_bytes()).hexdigest(),
        "transport_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "system_prompt": transport.SYSTEM_PROMPT,
        "socket_read_timeout_seconds": args.timeout,
        "workers": args.workers,
    }
    metadata_path = args.output / "configuration.json"
    metadata_text = json.dumps(metadata, indent=2) + "\n"
    if metadata_path.exists() and metadata_path.read_text() != metadata_text:
        parser.error("configuration differs from existing run")
    metadata_path.write_text(metadata_text)
    pending = [j for j in jobs if not (args.output / (j["job_id"] + ".json")).exists()]

    def execute(job: dict[str, str]) -> bool:
        started = time.perf_counter()
        result = {
            "job_id": job["job_id"],
            "kind": job["kind"],
            "prompt_sha256": hashlib.sha256(job["prompt"].encode()).hexdigest(),
        }
        try:
            payload, response = transport.api_call(
                endpoint, key, job["prompt"], config, args.timeout
            )
            result.update(request=payload, response=response)
            answer = parse_answer(transport.strip_reasoning(transport.response_text(response)))
            if job["kind"] == "judgment":
                if answer.get("verdict") not in ["consistent", "inconsistent", "undetermined"]:
                    raise ValueError("invalid judgment")
            elif not isinstance(answer.get("probes"), list) or len(answer["probes"]) > 12:
                raise ValueError("invalid probe response")
            result.update(status="completed", parsed=answer)
        except Exception as error:  # noqa: BLE001 - persist failures without leaking response headers.
            result.update(status="failed", error_type=type(error).__name__)
        result["seconds"] = time.perf_counter() - started
        (args.output / (job["job_id"] + ".json")).write_text(json.dumps(result, indent=2) + "\n")
        print(job["job_id"], result["status"], flush=True)
        return result["status"] == "completed"

    jobs_to_run = iter(pending[: args.limit])
    failed = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        active = set()
        for _ in range(args.workers):
            job = next(jobs_to_run, None)
            if job:
                active.add(pool.submit(execute, job))
        while active:
            done, active = concurrent.futures.wait(
                active, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                failed = not future.result() or failed
            if failed:
                print("batch failure: no new calls; persisting already-running calls", flush=True)
                continue
            for _ in done:
                job = next(jobs_to_run, None)
                if job:
                    active.add(pool.submit(execute, job))


if __name__ == "__main__":
    main()
