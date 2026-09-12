# IntentTester TDL 执行与表示审计 v0.1

> 日期：2026-09-01  
> 审计对象：[testmigrator/intenttest](https://github.com/testmigrator/intenttest)  
> 固定 commit：`a906b7c49bbe0dec4d1d8b911e97281b7ce63063`  
> 目的：判断 CoSMiT RQ1 能否运行实际 TDL 抽取，以及公开 TDL 是否直接提供可执行的迁移条款。

## 1. 结论

本轮完成了官方 artifact 的源码、构建和入口审计，但尚未获得实际 TDL 输出。因此，对 IntentTester 的 empirical information loss 仍应标记为 `undetermined`。

已经确认三点：

1. TDL 的公开 schema 以字符串描述 metadata、input、execution step 和 assertion；没有 typed precondition、observation、oracle parameter、environment 或跨实现 adapter 字段。
2. 抽取 prompt 明确要求“abstract away from specific code details”；VerificationAgent 仍由同一 LLM 判断 TDL 是否忠实，没有条款级执行验证。这说明 TDL 具有迁移关键信息不可机读、不可逐条款验证的结构性风险，但不能单凭 schema 断言信息必然丢失，因为 LLM 仍可能把细节写入字符串。
3. 当前公开 commit 不能按 README 直接完成端到端运行；在不修改上游源码的前提下，实际 TDL 输出还受模型凭据和 artifact 缺陷阻塞。

论文中可安全使用的表述是：

> IntentTester TDL is a structured natural-language representation. Its public schema can encode details as free text, but does not expose transport-critical clauses as typed, executable obligations. Whether a concrete TDL output retains each clause is therefore an empirical question evaluated by our controlled-pair study.

不能使用的表述是：

> IntentTester 必然丢失所有精确语义，或 CoSMiT 已经实证优于 IntentTester。

## 2. 表示层静态证据

### 2.1 TDL 字段

公开 `TestDescriptionLanguage` 只有：

- metadata：`testName`、`description`、`goal`；
- inputs：`content`、`contentType`；
- executionSteps：字符串 `stepDescription`；
- assertions：字符串 `description`。

Java parser 虽然对应的 entity 还声明了 execution input/output，但公开 parser 只写入 `stepDescription`。assertion 没有独立的 tolerance、exception type、dtype、shape relation、state relation 或 observation point 字段。

### 2.2 抽取与验证

`IntentAbstractorAgent` 将源测试和 TDL format 交给 LLM，要求输出 JSON，并要求抽象掉具体代码细节。`VerificationAgent` 再次调用同一 LLM，询问 TDL 是否忠实表达测试意图。该流程适合生成可读、语言无关的意图，但并不等价于：

- 验证两个实现之间的合法映射；
- 执行精确 oracle 条款；
- 证明某一条件边界内的性质保持；
- 生成能够反驳候选 adapter 的输入。

这正是 CoSMiT 的增量位置：TDL 用于候选生成和解释，Property IR/Adapter DSL 用于逐条款求解和反例验证。

## 3. 公开 artifact 执行审计

### 3.1 仓库与环境

- clone 后 HEAD 与论文审计基线一致：`a906b7c49bbe0dec4d1d8b911e97281b7ce63063`；
- README 要求 Python 3.9+、JDK 11+、Neo4j；
- `pom.xml` 实际指定 `maven.compiler.source/target=18`；
- LLMService 使用 DashScope，必须提供 `apiKey` 和 `modelName`；当前环境没有这两个值。

### 3.2 构建结果

- 用 JDK 11 构建：因目标版本 18 失败；
- 用 JDK 20 构建：Lombok 生成恢复，但源码仍有 6 个确定的编译错误；
- 主要缺失：`FileUtil.FileType` 与 `FileUtil.loadContentFromPath`，公开 `FileUtil.java` 中不存在这些成员；
- 用 Maven 默认 JDK 26 构建：除上述问题外，旧 Lombok 还导致大量 accessor/builder 符号缺失。

### 3.3 Python TDL 入口

直接执行 `python/step1_test_intent/tdl_main.py`：

```text
ModuleNotFoundError: No module named 'testreuse'
```

继续静态检查可见 `test_tdl_agent.py` 的 `generate_tdl_test_code` 还引用未定义的 `llm_model`。因此不能把 Python 入口作为未经修改的官方可运行 baseline。

### 3.4 审计解释

这些问题只说明公开 artifact 在当前 commit/环境下不可直接复现，不否定论文实验，也不授权我们修改后称为“official IntentTester”。正式实验必须分别报告：

1. `official artifact, unmodified`：原 commit 和失败日志；
2. `external run`：若作者提供环境/输出，按原样保存；
3. `style reproduction`：使用公开 prompt/schema 和固定模型生成，明确标注为复现版本；
4. `CoSMiT`：独立实现，不复制无许可证源码。

## 4. 已准备的 controlled-pair study

已建立 4 对、8 条可执行 PyTorch 测试，每对只改变一个会改变合法 adapter 集的条款：

| Pair | 固定高层目标 | 唯一变化 | adapter 差异 |
| --- | --- | --- | --- |
| ITC-001 | 整数求和并检查结果 | oracle 是否包含输出 dtype | 直接 reduce 与先 cast 再 reduce |
| ITC-002 | 检查浮点值接近 | `atol=1e-5` 或 `1e-6` | 目标 oracle 参数不同 |
| ITC-003 | squeeze axis 1 并检查 shape | 轴大小为 1 或非 1 | 直接 squeeze 与条件 identity |
| ITC-004 | 稀疏交叉熵 mean | 类别轴为 1 或最后一维 | 目标 input permutation 不同 |

8 条源测试均已执行通过。prompt renderer 逐字复现公开 `IntentAbstractorAgent.USER_PROMPT` 和 TDL format，已经生成 8 条 JSONL 输入及 SHA-256 manifest：

- `benchmark/feasibility/intenttester/controlled_collision_tests.py`
- `benchmark/feasibility/intenttester/cases.yaml`
- `benchmark/feasibility/intenttester/prompts.jsonl`
- `benchmark/feasibility/intenttester/prompt-manifest.json`

当前唯一必须外部补齐的环节是：固定模型和参数，运行三次 TDL 抽取并保存 raw response。之后由盲态标注者判断两条 TDL 是否保留唯一变化条款。

## 5. RQ1 决策规则

对每对输出使用四分类：

- `distinguishable`：两条 TDL 明确保留变化条款及其正确值，足以恢复不同 adapter；
- `collision`：变化条款被遗漏、合并或写错，无法从 TDL 区分合法 adapter；
- `invalid-output`：输出不可解析或与源测试矛盾；
- `undetermined`：只看 TDL 无法稳定判断。

实验必须报告三次运行的一致性；不能只挑选发生 collision 的一次输出。正式结果还需加入 30–50 条真实官方测试，而 controlled pairs 只负责建立因果性和最小反例。

## 6. 下一步

1. 获得合法 DashScope 模型配置，或请 IntentTester 作者提供 TDL raw outputs；
2. 在不修改 pair gold 的前提下运行 8×3 次抽取；
3. 由两名标注者盲审 clause retention，第三人仲裁；
4. 对真实官方测试重复相同协议；
5. 只有完成以上步骤，才把 `collisions.yaml` 中 `intenttester_tdl_result` 从 `undetermined` 改为实证结果。
