"""Run the recoverable KATRER LLM stages with provenance-preserving outputs.

The public KATRER artifact does not contain the graph/retrieval intermediates and
its QueryAns entry point is incomplete.  This runner therefore reconstructs the
published prompt stages from fixed source/target code and labels every output as
``KATRER-reproduction-variant`` rather than a strict KATRER rerun.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "benchmark/public_systems/katrer-reproduction-inputs.yaml"
DEFAULT_ENV_FILE = ROOT / ".env.njusehub"
DEFAULT_ARTIFACT_ROOT = ROOT / "artifacts/katrer-reproduction"
DEFAULT_SUMMARY = ROOT / "benchmark/public_systems/katrer-reproduction-results-v0.2.json"
SYSTEM_PROMPT = "You are an expert at writing python test cases."


@dataclass(frozen=True)
class ModelConfig:
    model_id: str
    temperature: float
    top_p: float
    presence_penalty: float
    max_tokens: int


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def strip_reasoning(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()


def extract_tag(text: str, tags: tuple[str, ...]) -> str | None:
    for tag in tags:
        match = re.search(
            rf"\[{re.escape(tag)}\](.*?)\[/{re.escape(tag)}\]",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
    return None


def clean_python_block(text: str) -> str:
    cleaned = strip_reasoning(text)
    tagged = extract_tag(cleaned, ("Reused_Test", "Migrated_Test"))
    if tagged is not None:
        cleaned = tagged
    fenced = re.search(r"```(?:python)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1)
    return cleaned.strip() + "\n"


def extract_definition(path: Path, name: str, limit: int | None = None) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == name
        ):
            segment = ast.get_source_segment(source, node) or ""
            if limit is not None and len(segment) > limit:
                raise ValueError("explicit context limit would truncate a definition")
            return segment
    raise ValueError(f"definition {name!r} not found in {path}")


def remove_unused_top_level_defs(source: str) -> str:
    """Mirror KATRER PromptGeneration.find_unused_top_level_defs."""
    tree = ast.parse(source)
    all_defs = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        and not node.name.lower().startswith("test")
    }
    usage = {name: 0 for name in all_defs}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in usage:
            usage[node.id] += 1
    unused = {name for name, count in usage.items() if count == 0}
    tree.body = [
        node
        for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef)) or node.name not in unused
    ]
    ast.fix_missing_locations(tree)
    return ast.unparse(tree).replace("\n\n", "\n")


def format_symbol_context(symbols: list[dict[str, str]], root: Path) -> str:
    blocks: list[str] = []
    for symbol in symbols:
        path = root / symbol["path"]
        definition = extract_definition(path, symbol["name"])
        blocks.extend(
            [
                "[FuncName]",
                symbol["qualified_name"],
                "[/FuncName]",
                "[CodeContent]",
                definition,
                "[/CodeContent]",
            ]
        )
    return "\n".join(blocks)


def build_generation_prompt(case: dict[str, Any], root: Path) -> tuple[str, str]:
    source_path = root / case["source_test_path"]
    source = source_path.read_text(encoding="utf-8")
    normalized_source = remove_unused_top_level_defs(source)
    source_context = format_symbol_context(case["source_symbols"], root)
    target_context = format_symbol_context(case["target_symbols"], root)
    source_library = case["source_library"]
    target_library = case["target_library"]
    prompt = f"""[Src_Test]
{normalized_source}
[/Src_Test]
Test Intention clarifies source test purpose.
[TestIntention]
{source_context}
[/TestIntention]
Followings are relevant code contexts in the target repository.
[TarCodeContexts]
{target_context}
[/TarCodeContexts]
Given a source test annotated with the tag [Src_Test], its test intention annotated with the tag [TestIntention], and API definitions in the target library annotated with the tag [TarCodeContexts],
your task is to reuse tests across Python libraries to uncover potential bugs, now from '{source_library}' to '{target_library}', adding corner case parameters when possible, by following these steps:
1. Understand the source test via [Src_Test] and [TestIntention].(e.g., test objectives, expected behaviors, etc.)
2. Understand APIs definitions in the target library via [TarCodeContexts], and rewrite each test case one by one in the test class, substituting source APIs with the corresponding target APIs.
3. Preserve test semantics and adapt parameter lists for each test case if needed due to various reasons.(e.g., different backends, missing (decorator) function equivalent implementations, etc.)
4. For any test case that can't be reused, still remain the test case but with its body as '''\n    pass  # Functionality Inconsistency''' as the reused test.
5. Use strict output format without additional explanations:
[Reused_Test]
# Reused Test
[/Reused_Test]"""
    return prompt.replace("\n\n", "\n"), normalized_source


def build_judgement_prompt(source: str, candidate: str) -> str:
    return f"""Determine whether the test intent maintains after test reuse (Source-Repository Tests V.S. Target-Repository Tests).
[Source-Repository Tests]
{source}
[/Source-Repository Tests]
[Target-Repository Tests]
{candidate}
[/Target-Repository Tests]
Note that differences across libraries (e.g., backend-related parameter variations) may lead to mismatches in test input details, so please focus on whether the test intent is consistent in the aspect of core functionalities instead. Respond strictly using one of the following options: "Consistent" or "Inconsistent", enclosed within the tags below:
[ConsistencyAnswer]
Your_Answer
[/ConsistencyAnswer]"""


def api_call(
    base_url: str,
    api_key: str,
    prompt: str,
    config: ModelConfig,
    timeout: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = {
        "model": config.model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": config.temperature,
        "top_p": config.top_p,
        "presence_penalty": config.presence_penalty,
        "max_tokens": config.max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    cafile = os.environ.get("SSL_CERT_FILE")
    if not cafile:
        try:
            import certifi

            cafile = certifi.where()
        except ImportError:
            cafile = None
    ssl_context = ssl.create_default_context(cafile=cafile)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as response:
            content_parts: list[str] = []
            reasoning_parts: list[str] = []
            model = config.model_id
            finish_reason = None
            usage = None
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:") :].strip()
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                model = str(chunk.get("model") or model)
                if chunk.get("usage"):
                    raw_usage = chunk["usage"]
                    usage = {
                        key: raw_usage.get(key)
                        for key in ("prompt_tokens", "completion_tokens", "total_tokens")
                        if key in raw_usage
                    }
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                choice = choices[0]
                delta = choice.get("delta") or {}
                if delta.get("reasoning_content"):
                    reasoning_parts.append(str(delta["reasoning_content"]))
                if delta.get("content"):
                    content_parts.append(str(delta["content"]))
                if choice.get("finish_reason") is not None:
                    finish_reason = choice["finish_reason"]
            result = {
                "model": model,
                "choices": [
                    {
                        "finish_reason": finish_reason,
                        "message": {
                            "role": "assistant",
                            "reasoning_content": "".join(reasoning_parts),
                            "content": "".join(content_parts),
                        },
                    }
                ],
                "usage": usage,
                "transport": "openai-compatible-sse",
            }
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"model endpoint returned HTTP {error.code}: {body[:500]}") from error
    validate_response(result)
    return payload, result


def validate_response(response: dict[str, Any]) -> None:
    """Reject interrupted, truncated and non-text outputs before extraction."""
    choices = response.get("choices") or []
    if not choices or choices[0].get("finish_reason") != "stop":
        raise RuntimeError("response did not terminate with stop")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("response contains no text content")
    if content.lower().count("<think>") != content.lower().count("</think>"):
        raise RuntimeError("response contains an unclosed reasoning block")


def api_call_with_retries(
    base_url: str,
    api_key: str,
    prompt: str,
    config: ModelConfig,
    timeout: int,
    retries: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return api_call(base_url, api_key, prompt, config, timeout)
        except (RuntimeError, TimeoutError, urllib.error.URLError) as error:
            last_error = error
            if attempt == retries:
                break
            print(f"model call incomplete; retrying ({attempt + 1}/{retries})", flush=True)
    assert last_error is not None
    raise last_error


def response_text(response: dict[str, Any]) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError("response content must be text")
        return content
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("response does not contain choices[0].message.content") from error


def syntax_status(code: str) -> tuple[str, str | None]:
    try:
        ast.parse(code)
    except SyntaxError as error:
        return "invalid", f"{error.msg} (line {error.lineno})"
    return "valid", None


def target_binding_status(code: str, target_library: str) -> bool:
    """Legacy import-only signal; callers must not label it operation binding."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name.split(".")[0] == target_library for alias in node.names
        ):
            return True
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.split(".")[0] == target_library
        ):
            return True
    return False


def test_candidate_issues(code: str) -> list[str]:
    """Conservative intake gates, not pytest collection or semantic validation."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ["syntax-error"]
    tests = [
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
    ]
    if not tests:
        return ["no-recognizable-tests"]
    issues = []
    for test in tests:
        if test.decorator_list:
            issues.append("decorated-test-requires-collection")
        if not any(isinstance(n, (ast.Call, ast.Assert)) for n in ast.walk(test)):
            issues.append("empty-test")
    if any(
        isinstance(n, ast.Attribute) and n.attr in {"skip", "skipif", "xfail"}
        for n in ast.walk(tree)
    ):
        issues.append("skipped-or-xfailed-test")
    return sorted(set(issues))


def judgement_value(text: str) -> str:
    cleaned = strip_reasoning(text)
    tagged = extract_tag(cleaned, ("ConsistencyAnswer",))
    value = (tagged or cleaned).strip().lower()
    if value == "consistent":
        return "consistent"
    if value == "inconsistent":
        return "inconsistent"
    return "undetermined"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_case(
    case: dict[str, Any],
    root: Path,
    run_dir: Path,
    base_url: str,
    api_key: str,
    config: ModelConfig,
    timeout: int,
    retries: int,
) -> dict[str, Any]:
    case_dir = run_dir / case["case_id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    prompt, source = build_generation_prompt(case, root)
    (case_dir / "generation-prompt.txt").write_text(prompt + "\n", encoding="utf-8")

    started = time.monotonic()
    request_payload, generation_response = api_call_with_retries(
        base_url, api_key, prompt, config, timeout, retries
    )
    generation_seconds = time.monotonic() - started
    write_json(case_dir / "generation-request.json", request_payload)
    write_json(case_dir / "generation-response.json", generation_response)
    raw_generation = response_text(generation_response)
    candidate = clean_python_block(raw_generation)
    (case_dir / "candidate.py").write_text(candidate, encoding="utf-8")

    judge_prompt = build_judgement_prompt(source, candidate)
    (case_dir / "judgement-prompt.txt").write_text(judge_prompt + "\n", encoding="utf-8")
    started = time.monotonic()
    judge_request, judge_response = api_call_with_retries(
        base_url, api_key, judge_prompt, config, timeout, retries
    )
    judgement_seconds = time.monotonic() - started
    write_json(case_dir / "judgement-request.json", judge_request)
    write_json(case_dir / "judgement-response.json", judge_response)
    judge_text = response_text(judge_response)
    syntax, syntax_error = syntax_status(candidate)
    target_bound = target_binding_status(candidate, case["target_library"])

    record = {
        "case_id": case["case_id"],
        "producer": case["producer_label"],
        "semantic_dimension": case["semantic_dimension"],
        "source_property": case["source_property"],
        "source_test_path": case["source_test_path"],
        "generation_prompt_sha256": sha256_text(prompt),
        "candidate_sha256": sha256_text(candidate),
        "candidate_code": candidate,
        "syntax": syntax,
        "syntax_error": syntax_error,
        "target_import_signal": "observed" if target_bound else "not-observed",
        "intake_issues": test_candidate_issues(candidate),
        "property_evidence_state": "undetermined",
        "llm_consistency_judgement": judgement_value(judge_text),
        "generation_seconds": round(generation_seconds, 3),
        "judgement_seconds": round(judgement_seconds, 3),
        "dynamic_execution": "unavailable-target-runtime",
        "property_check": "pending",
        "artifact_directory": str(case_dir.relative_to(root)),
    }
    write_json(case_dir / "record.json", record)
    return record


def run_judgement_only(
    case: dict[str, Any],
    previous_record: dict[str, Any],
    root: Path,
    run_dir: Path,
    base_url: str,
    api_key: str,
    config: ModelConfig,
    timeout: int,
    retries: int,
) -> dict[str, Any]:
    case_dir = run_dir / case["case_id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    _, source = build_generation_prompt(case, root)
    candidate = str(previous_record["candidate_code"])
    (case_dir / "candidate.py").write_text(candidate, encoding="utf-8")
    judge_prompt = build_judgement_prompt(source, candidate)
    (case_dir / "judgement-prompt.txt").write_text(judge_prompt + "\n", encoding="utf-8")
    started = time.monotonic()
    judge_request, judge_response = api_call_with_retries(
        base_url, api_key, judge_prompt, config, timeout, retries
    )
    judgement_seconds = time.monotonic() - started
    write_json(case_dir / "judgement-request.json", judge_request)
    write_json(case_dir / "judgement-response.json", judge_response)
    updated = dict(previous_record)
    updated["llm_consistency_judgement"] = judgement_value(response_text(judge_response))
    updated["judgement_seconds"] = round(judgement_seconds, 3)
    updated["candidate_origin_artifact"] = previous_record.get(
        "candidate_origin_artifact", previous_record["artifact_directory"]
    )
    updated["artifact_directory"] = str(case_dir.relative_to(root))
    write_json(case_dir / "record.json", updated)
    return updated


def enrich_cases(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    source_library = manifest["upstream"]["source_library"]["name"]
    target_library = manifest["upstream"]["target_library"]["name"]
    producer_label = manifest["producer_label"]
    cases = []
    for raw_case in manifest["cases"]:
        case = dict(raw_case)
        case["source_library"] = source_library
        case["target_library"] = target_library
        case["producer_label"] = producer_label
        cases.append(case)
    return cases


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--stage", choices=("all", "judgement"), default="all")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    manifest_path = args.manifest.resolve()
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    cases = enrich_cases(manifest)
    if args.case_id:
        wanted = set(args.case_id)
        cases = [case for case in cases if case["case_id"] in wanted]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        raise SystemExit("no cases selected")

    model_raw = manifest["model"]
    config = ModelConfig(
        model_id=str(model_raw["id"]),
        temperature=float(model_raw["temperature"]),
        top_p=float(model_raw["top_p"]),
        presence_penalty=float(model_raw["presence_penalty"]),
        max_tokens=int(model_raw["max_tokens"]),
    )
    for case in cases:
        build_generation_prompt(case, ROOT)
    if args.dry_run:
        print(f"validated {len(cases)} case(s); no model calls made")
        return 0

    load_env_file(args.env_file.resolve())
    base_url = os.environ.get("NJUSEHUB_BASE_URL", "").strip()
    api_key = os.environ.get("NJUSEHUB_API_KEY", "").strip()
    if not base_url or not api_key:
        raise SystemExit("NJUSEHUB_BASE_URL and NJUSEHUB_API_KEY are required")

    now = datetime.now(timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.artifact_root.resolve() / run_id
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.retries < 0:
        raise SystemExit("--retries must be non-negative")
    summary_path = args.summary.resolve()
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    previous: dict[str, Any] | None = None
    if summary_path.exists():
        candidate_previous = json.loads(summary_path.read_text(encoding="utf-8"))
        if candidate_previous.get("manifest_sha256") == manifest_sha256:
            previous = candidate_previous
    previous_by_id = {record["case_id"]: record for record in (previous or {}).get("records", [])}
    if args.stage == "judgement":
        missing = [case["case_id"] for case in cases if case["case_id"] not in previous_by_id]
        if missing:
            raise SystemExit(f"judgement-only requires existing candidates: {missing}")
    new_records = []

    def execute(case: dict[str, Any]) -> dict[str, Any]:
        if args.stage == "judgement":
            print(f"[{case['case_id']}] judgement retry started", flush=True)
            record = run_judgement_only(
                case,
                previous_by_id[case["case_id"]],
                ROOT,
                run_dir,
                base_url,
                api_key,
                config,
                args.timeout,
                args.retries,
            )
            print(f"[{case['case_id']}] judgement retry completed", flush=True)
            return record
        print(f"[{case['case_id']}] generation started", flush=True)
        record = run_case(
            case,
            ROOT,
            run_dir,
            base_url,
            api_key,
            config,
            args.timeout,
            args.retries,
        )
        print(f"[{case['case_id']}] generation and judgement completed", flush=True)
        return record

    if args.workers == 1:
        new_records = [execute(case) for case in cases]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(execute, case): case for case in cases}
            for future in concurrent.futures.as_completed(futures):
                new_records.append(future.result())

    records_by_id = {record["case_id"]: record for record in (previous or {}).get("records", [])}
    records_by_id.update({record["case_id"]: record for record in new_records})
    case_order = [case["case_id"] for case in enrich_cases(manifest)]
    records = [records_by_id[case_id] for case_id in case_order if case_id in records_by_id]
    run_ids = list((previous or {}).get("run_ids", []))
    if not run_ids and previous and previous.get("run_id"):
        run_ids.append(previous["run_id"])
    run_ids.append(run_id)

    summary = {
        "schema_version": "0.2",
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "context_hashes": {
            symbol["path"]: hashlib.sha256((ROOT / symbol["path"]).read_bytes()).hexdigest()
            for case in cases
            for symbol in case["source_symbols"] + case["target_symbols"]
        },
        "dataset": manifest["dataset"],
        "producer": manifest["producer_label"],
        "latest_run_id": run_id,
        "run_ids": list(dict.fromkeys(run_ids)),
        "created_at": (previous or {}).get("created_at", now.isoformat()),
        "updated_at": now.isoformat(),
        "manifest_path": str(manifest_path.relative_to(ROOT)),
        "manifest_sha256": manifest_sha256,
        "upstream": manifest["upstream"],
        "model": model_raw,
        "limitations": manifest["limitations"],
        "records": records,
    }
    write_json(summary_path, summary)
    print(f"wrote {len(records)} cumulative record(s) to {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
