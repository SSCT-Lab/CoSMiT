# Public-System Candidate Batch

本目录把 migration system 与 CoSMiT 的职责分开：IntentTester/KATRER 负责产生候选，CoSMiT 只导入原始输出、绑定独立性质并进行认证。

## 当前入口

```bash
python3 benchmark/public_systems/import_intenttester_candidates.py
python3 benchmark/public_systems/scan_target_binding.py
python3 benchmark/public_systems/run_intenttester_execution_sample.py
python3 benchmark/public_systems/run_intenttester_replay.py
python3 benchmark/public_systems/validate_public_candidates.py
python3 benchmark/public_systems/katrer_reproduction.py --dry-run
python3 benchmark/public_systems/katrer_property_check.py
```

导入器不会复制 IntentTester 的候选代码，只保存固定 checkout 中的相对路径、SHA-256、语言、TDL 元数据和静态语法状态。`intenttester-review-sample.yaml` 使用 candidate code hash 做每个迁移方向三条的确定性抽样，抽样前不读取 CoSMiT 输出。

`intenttester-target-binding-scan.json` 是静态资格筛查，不是语义 verdict。`intenttester-execution-sample.json` 保存 40 条候选的隔离 pytest 结果；`intenttester-replay.json` 包含四条 provisional source-property qualification 案例。

`reproduction-status.yaml` 区分三种状态：official pipeline rerun、published-output replay 和 externally blocked。KATRER 仓库中出现的 NaiRAG/NaiGen 输出属于论文 baseline，不能标记为 KATRER candidates。

`katrer_reproduction.py` 使用固定的 NumPy 2.3.0/CuPy 13.5.1 源码上下文和论文中的 DeepSeek-R1 参数，恢复 KATRER 可公开确认的 generation 与 consistency-judgement 阶段。由于公开仓库缺少 KG/检索中间产物、`Check` 模块和可工作的 `QueryAns.py` 入口，其结果统一标记为 `KATRER-reproduction-variant`，不得写成严格端到端复现。密钥从根目录 `.env.njusehub` 读取，任何请求产物均不保存 Authorization header。

`katrer_property_check.py` 独立重放 source tests，并收集候选 AST 和固定 CuPy 源码线索；静态线索不能产生正向认证。没有目标执行证据时保持未决；KATRER 的 LLM 一致性判断不作为最终证书。

## 发布边界与本地配置

公开仓库不包含原始模型响应、运行日志、生成结果 JSON、第三方 checkout 或运行环境。文档中的历史结果路径指本地实验材料，并非随仓库提供的完整复现包。应先取得固定版本的上游材料，再按上述入口生成本地索引和结果。唯一保留的审计 JSON 是不含凭据的负向回归测试 fixture，不代表正式效果评估。

运行上游审计时，通过 `JAVA_HOME` 指定 JDK，通过 `COSMIT_KATRER_PYTHON` 指定论文要求的 Python 解释器；不再使用个人机器绝对路径。模型凭据仅保存在 git-ignored 的本地环境文件或进程环境中，不能提交。完整方法复现仍受上游 artifact 可用性约束。
