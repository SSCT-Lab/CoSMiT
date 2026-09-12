# RQ 开发实验入口

对应桌面研究计划第 6 页的 RQ1/RQ2/RQ3。当前是**参数化受控开发实验**，不是完整论文评估。不要把结果作为 held-out/gold 性能表。

## 已实现的部分

- `src/cosmit/engine/certification.py`：独立前置条件、源／目标观察、value/dtype/shape/exception/outcome 条款比较、预算搜索、两次反例复验、受限缩减、候选条件的独立样本重检。
- `kernels.py`：真实调用 PyTorch/TensorFlow 的参数化操作。每次探针都执行这些程序，不读取预先写好的 verdict。
- `subjects.py`：由已有 12 条性质派生的开发域、24 个参考／人工错误程序、历史 witness 与三种输入策略。随机状态性质 CCP-025 尚未接入；原 13 条性质账本不改。
- `run_development.py`：固定版本、CPU/单线程、4 策略 × 24 程序 × 10 seeds。manifest 先于执行保存，逐 campaign 保存 JSONL。
- `prepare_review.py`：将程序中的 family/adapted 常量特化，输出不含来源标签、系统判定、反例和建议条件的人工复核包；答案映射放在目录外。
- `run_llm_baselines.py`：同一盲态材料下的 direct judgment 与 source-only JSON 探针对照；只有 `--execute` 才调用服务；失败停止、不自动重试。
- `validate_run.py`：校验文件哈希、任务完整性、预算、复验门槛、汇总一致性与条件训练／验证分离。
- `src/cosmit/engine/mapping_ir.py`：提取候选的显式调用、参数、cast／transpose 等结构，并保留 residual code；仅作为语法信息，不认证控制流或运行时绑定。
- `verify_review_programs.py`：在执行前验证复核材料对应仓库自身生成的 fixture，检查常量特化后的源／目标程序与原始注册函数输出一致。不运行模型生成代码。
- `evaluate_llm.py`：将 LLM 生成的数据输入送入同一受信任 kernel，保留非法输入和缺失输出；直接判断与已有反例的冲突单列，不计算 gold accuracy。

## 执行命令

从仓库根目录，使用已有 Python 3.10.9 / NumPy 2.1.3 / PyTorch 2.9.1 / TensorFlow 2.20.0 环境：

```bash
PYTHONPATH=src python3 benchmark/rqs/run_development.py --seeds 10 --budget 12
python3 benchmark/rqs/validate_run.py artifacts/research-rqs/20260909T091129697689Z --check-current-sources
python3 -m pytest -q
```

每次生成独立 run 目录，不覆盖前次结果。`--check-current-sources` 用于代码未变化时确认精确源码版本；修改代码后应新开 run，不能重写旧哈希。

目前选定开发 run：`artifacts/research-rqs/20260909T091129697689Z`。历史较早目录是试跑／代码迭代记录，不是新增独立样本。

人工复核：仅向复核者提供 `benchmark/rqs/review-v0.2/packet.json`，不要提供目录外的 `review-v0.2-key.json`、实验结果或旧 reference/mutant 标签。所有 reviewer 字段当前为空。`review/` 是域描述补全前的初版，不用于正式复核。

## 预算与判定含义

一个 execution unit 是一对源／候选执行。每 campaign 最多 12 对；两次复验也计入这 12 对。非法建议输入不调用程序但保留日志；源／目标环境错误为未决。缩减单独最多 24 次评估，与发现预算分开。条件选择使用 40 个 discovery 输入，另用不重合的 40 个 validation 输入评估，每条模板至少保留 3 个输入与 20% 的样本。

`supported-on-tested-inputs` 只说明日志中的输入通过所选条款，并不证明声明域正确。`registered-target-operation` 是受信任 fixture 的人工注册前提，不是自动目标调用证明；未登记则返回未决。该执行器不能直接安全运行任意模型生成代码，也不声称已自动恢复其 Mapping IR。

输入域是对先前固定 witness 的参数化开发扩展，必须重新复核。许多先前参考候选只在 witness 上有效，不能自动作为新域 gold。浮点比较沿用 `atol=1e-7, rtol=0`，发现偏差后没有事后放宽阈值。

策略 `original` 是先前手工挑选的 feasibility witness，不是官方原始回归输入，因此其全部命中是预期 sanity check。`clause-aware` 是按来源条款选择模板的第一版策略，不是完整分歧／成本排序算法。重复的确定性 seeds 不是独立统计样本。

## 尚不能据此报告的指标

- gold precision/recall、gold false-rejection：缺独立标签和官方／真实迁移对照。
- 相对完整 LLM／官方回归输入的主实验优势：对照尚未全部完成。
- root-cause accuracy：当前只输出失败的已声明条款，根因保持 undetermined。
- condition-boundary precision/recall：仅检验人工登记的条件模板，无独立全域边界真值。
- 自动候选 Mapping IR 恢复、随机状态覆盖、全部 40–60 条规则、ONNX 官方映射和真实 issue/PR 价值：仍需实现或补充证据。

更详细的任务状态见 `docs/research-rq-progress-2026-09-09.md`。

后续待办与验收见 [论文剩余任务](../../docs/research-remaining-tasks.md)。公开仓库不包含原始 run、模型响应和盲评答案；上述历史路径指本地生成产物，获取与发布边界见 [发布说明](../../docs/repository-publication.md)。
