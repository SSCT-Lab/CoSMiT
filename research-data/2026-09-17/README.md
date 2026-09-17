# Registered experiment results — 2026-09-17

This is the public, sanitized observation export for the completed CoSMiT campaign. It supports recounting observations, checking recorded decisions, and auditing missing results. It is **not** a standalone exact rerun package, independent gold annotation set, or anonymous submission artifact.

| Partition | Candidates | Paired executions | Primary model calls | Structured decisions | Failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| Constructed controls | 10 | 60 | 50 | 36 | 14 |
| Public discovery | 69 | 13,248 | 345 | 201 | 144 |
| Reserved operation families | 12 | 2,304 | 60 | 41 | 19 |

The 81 public candidates cover 30 operation families from a 1,401-counterpart inventory. Aliases, directions, inputs, and repetitions are correlated, not independent candidate samples. Both CoSMiT and the same-input DLLens comparator found the same trunc counterpart error; no incremental discovery was observed. The reserved families produced no counterexample. TransFuzz is a method reference only, not a baseline.

There are 455 primary requests and 33 separately recorded, one-time transport retries. The latter produce 17 additional structured decisions, yielding 295 available decisions and 160 failures in the retry view. The independent offline parsing sensitivity view recovers seven primary decisions (285 available / 170 failed). These views are separate and never replace primary outcomes. A structured decision does not mean a correct decision. Public trace-LLM candidates have zero valid primary judgments; this configuration cannot support a semantic accuracy comparison.

## Files and verification

- `*/cases.json`: registered numerical inputs, source/target API metadata, contract, verdicts, and original source/result hashes. Third-party function bodies are omitted; their hashes and upstream paths are retained.
- `*/executions.jsonl.gz`: one record per candidate/input/repetition, including observed source/target values, shape/dtype, source reference checks and clause outcomes. Read with Python `gzip.open(path, 'rt')`; ordinary JSON numeric semantics apply.
- `model-primary.json`, `model-retry.json`: request identity, prompt hash, parsed decision, failure type, termination status, usage when available, and original record hash. Model prose/reasoning and full prompts are omitted.
- `*/format-sensitivity.json`, `*/retry-view.json`: per-job status of the two supplemental views.
- `method-matrices.json`, `summary.json`, `cost.json`: aggregate results and interpretation boundaries.
- `configuration-*.json`: execution model parameters and code hashes. The controls configuration records the five-request C001 sub-batch; the other 45 calls are recorded separately in the primary ledger.
- `supplements/`: BESSER source/model alignment and TensorScope conversion observations.
- `upstream-lock.json`: fixed upstream repositories/commits and original acquisition status. Its `formal_experiment_status: not-run` is historical acquisition metadata; the completed campaign status is in `summary.json`.
- `SHA256.json`: hashes of every published data file, including this README.

From the repository root, verify hashes, execution identities and request accounting without model calls or framework installation:

```bash
python benchmark/baselines/export_public_results.py research-data/2026-09-17 --verify
```

To regenerate this export from the retained local raw archive, supply a **new** output directory without `--verify`. The exporter does not modify raw archives. Rerunning the underlying experiments additionally requires fixed upstream checkouts, framework environments, and model access; see [baseline procedures](../../benchmark/baselines/README.md). Those dependencies are not needed to inspect these results.

The export omits credentials, local identifying paths, third-party program/prompt bodies whose redistribution terms are not established, model prose, weights, environments and review answer keys. Original byte-level records remain in the local frozen archives, linked by hashes. This is an explicit publication boundary, not a claim that the omitted material is available from this repository.

The 488 calls report 1,881,002 tokens where usage exists; 124 calls lack complete usage and total billing is unknown. Call duration spanning the user-requested pause includes that pause. No broad preservation guarantee, formal accuracy, FSE readiness, or superiority is established by these results.
