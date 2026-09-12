# CoSMiT Feasibility Seed

该目录保存 PyTorch 2.9.1 → TensorFlow 2.20.0 的首批 10 条 provisional properties、官方证据、表示审计、collision records 和动态 trace。

复现实验：

```bash
TF_CPP_MIN_LOG_LEVEL=3 python3 benchmark/feasibility/run_seed_probes.py
```

输出应与 `dynamic-trace.json` 相同，其中 10 个 `adapted_preserves` 均为 `true`，10 个 `naive_preserves` 均为 `false`。

文件说明：

- `manifest.yaml`：范围、版本和 API groups；
- `properties.yaml`：10 条 provisional Property IR 和 adapter；
- `evidence.yaml`：固定 commit 的官方源码证据；
- `representations.yaml`：四种表示的 feasibility proxy audit；
- `collisions.yaml`：goal-only abstraction 下的可执行 collision；
- `exclusions.yaml`：无效 oracle、错误 adapter 和禁止的结果解释；
- `run_seed_probes.py`：可重复探针；
- `dynamic-trace.json`：冻结环境中的原始输出。

限制：本数据尚未经过独立 annotator B 复核，TDL-style 为手工 proxy，不能作为 IntentTester 基线结果。完整结论见 `docs/feasibility-report-v0.1.md`。

