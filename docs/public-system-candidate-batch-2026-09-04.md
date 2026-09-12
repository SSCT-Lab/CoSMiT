# CoSMiT Public-System Candidate Batch v0.1

日期：2026-09-04

> 2026-09-08 审计更新：本文保留当时状态。此后已保存 3 条 KATRER-inspired generation/judge 样例，但不是完整 KATRER 复现；三条性质状态均未决。旧检查器对 NC-001 的静态支持结论不再采信。当前证据、缺陷与后续优先级见 [审计清单](results-audit-2026-09-08.md)。

## 结论

本批次已经建立“真实系统输出 → 独立性质 → 隔离执行 → 条款判定”的第一条链路，但两个 producer 的可复现状态不同：

| System | Official pipeline rerun | Published output replay | 当前用途 |
| --- | --- | --- | --- |
| IntentTester | externally blocked | available | 已导入 5,531 个真实发布候选，首批 4 条完成性质资格检验 |
| KATRER | externally blocked | unavailable | 保存复现阻塞证据；暂不能生成或导入可归因于 KATRER 的候选 |

这里的 `externally blocked` 只描述公开 artifact 在当前固定环境下的状态，不否定论文中的原始实验结果。

## IntentTester

固定仓库：`testmigrator/intenttest@a906b7c49bbe0dec4d1d8b911e97281b7ce63063`。

未修改运行结果：

- JDK 20 Maven 构建失败：公开 `FileUtil` 缺少被调用的 `FileType` 与 `loadContentFromPath`，共形成 6 个编译错误；
- Python TDL 入口失败：`ModuleNotFoundError: No module named 'testreuse'`；
- 配置要求 DashScope `apiKey/modelName`，当前复现环境未提供；
- 仓库没有观察到许可证文件，因此 CoSMiT 只保存路径、哈希和评估元数据，不复制候选代码。

公开结果导入：

- 5,531 个 `test_prompt_result` 候选，覆盖 18 个迁移方向；
- 3,371 个 Java、2,148 个 Python、10 个 JavaScript、2 个缺少代码 fence；
- 4,929 个配套 TDL 可以解析；
- 2,122 个 Python 候选通过 AST 语法检查，26 个存在语法错误；
- 以 candidate code SHA-256 排序，每个方向固定抽取 3 条，共 54 条盲态 review sample。

针对目标包名唯一明确的 Python 方向执行了静态 target-binding scan。两个 simplejson 方向共 680 个候选，其中 659 个为语法有效 Python；0/659 观察到 `simplejson` import。626 个显式导入 stdlib `json`，其余使用 placeholder 或没有目标模块 import。该扫描只作为候选资格信号，不能在 source-property 对齐和人工复核前直接记为语义错误。

从两个 simplejson 方向各取 code SHA-256 最低的 20 条语法有效候选，在隔离环境中执行 pytest：29/40 通过候选自身测试，8/40 发生断言或测试期失败，3/40 在导入/收集阶段失败；0/40 观察到 `simplejson` import。这个结果用于区分 execute-only 与 target-operation-binding，不代表完整性质保持率。

## 首批性质资格检验

首批选择 nanojson/gson → simplejson 的四个候选。源条款通过 nanojson 的 JUnit4 历史源码和 Gson 官方测试独立恢复，目标 witness 使用 simplejson 3.20.1；候选在 macOS `sandbox-exec` 中执行，禁止网络和临时目录以外的写入。

| Property | Source clause | Candidate self-test | Target reference | Target operation binding |
| --- | --- | --- | --- | --- |
| IT-PROP-001 | 解析数组并取得索引 4 对象中的 `abc=123` | pass | simplejson 返回 123 | refuted：候选导入 stdlib `json` |
| IT-PROP-002 | 整数值对应的 `isNull("key")` 为 false | pass | simplejson 返回 non-null | refuted：候选导入 stdlib `json` |
| IT-PROP-003 | builder 中 boolean true 的 JSON 序列化 | pass | simplejson 返回 `[true]` | refuted：候选导入 stdlib `json` |
| IT-PROP-004 | 无引号多词输入应触发 JSON 解析异常 | import failure | simplejson 抛出 `JSONDecodeError` | refuted：候选导入不存在的 `decoder`，且未绑定 simplejson |

前三条说明“候选自己的测试通过”仍可能没有测试目标库，第四条说明 target operation 未绑定时还会直接导入失败。当前状态是 provisional qualification evidence，而不是 IntentTester 错误率：公开结果包未声明精确 source commits，source-to-split-test 对齐和 target-operation obligation 仍需独立复核。

## KATRER

固定仓库：`Davidoxn/KATRER@c28ebfca5e309cdf0be794ae0ab388c8f547fba4`，MIT License。

已完成的实际检查：

- KATRER 目录中的 15 个 Python 脚本在公开建议的 Python 3.12 环境下通过语法编译；
- `QueryAns.py` 实际执行失败：缺少仓库未提供的 `Check` 模块；
- `QueryAns.py` 定义了 `call_llm_api`，但入口路径对它的调用次数为 0，当前入口是在读取和判断已有答案；
- 脚本仍包含 `/path2/` 硬编码和 `Your_API_Key_Here`；
- 公开 checkout 不包含 KATRER 的 `res_gpu`、`judge_ans`、`test_res`；其中出现的 NaiRAG/NaiGen 文件只能归属于 baseline；
- README 指向的 Zenodo 17140838 为 `restricted`，API 返回 0 个公开文件，无法取得 GPU Docker image 或 KATRER 结果。

因此当前不能产生可诚实标记为 `producer=KATRER` 的候选。继续条件是获得受限 replication package，或得到作者确认的模型、数据、镜像和输出；在此之前可运行的 KATRER-style prompt 只能作为独立 reproduction variant，不能替代 KATRER。

## 复现入口

```bash
python3 benchmark/public_systems/audit_system_reproduction.py
python3 benchmark/public_systems/import_intenttester_candidates.py
python3 benchmark/public_systems/scan_target_binding.py
python3 benchmark/public_systems/run_intenttester_execution_sample.py
python3 benchmark/public_systems/run_intenttester_replay.py
python3 benchmark/public_systems/validate_public_candidates.py
```

## 下一批

1. 对首批四条完成独立复核，决定是否进入真实候选结果表；
2. 从 54 条冻结样本中扩展 JSON、HTML、Time 三个 domain，每条先恢复 source clause，再执行目标候选；当前额外 40 条只完成 execute-only 层，不得冒充性质认证；
3. 将 `target-operation-binding` 纳入 Property IR/obligation schema，防止只验证候选内部自洽；
4. 获得 KATRER replication package 或合法模型配置后，再生成 KATRER candidates；
5. 分层报告 syntax failure、execution failure、target bypass、property refutation 和 undetermined，禁止合并成单一 pass rate。
