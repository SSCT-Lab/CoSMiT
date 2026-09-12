# CoSMiT Candidate-Certification Annotation Guide v0.2

> 状态：pilot 冻结候选；替代 feasibility guide v0.1 用于后续 12–15 API groups。  
> 核心任务：给定证据支持的源性质与候选目标迁移，标注候选在声明范围内是否保持性质，以及失败原因和可成立条件。

## 1. 基本单位

基本单位是一个 `certification case`，由以下三部分组成：

1. 原子源性质 `property`：仅包含一个主要 observation 和一个可判定 oracle；
2. 候选目标迁移 `candidate`：来自公开系统、真实迁移/维护记录或受控 mutation；
3. 声明验证范围 `scope`：输入域、环境、执行预算和观测模型。

同一源性质可以对应多个候选，但每个候选必须独立记录，不能用“该 API 可迁移”替代候选级判定。

## 2. 必填结构

```yaml
case_id:
property_id:
group_id:
split: development | evaluation-holdout
source_evidence: []
target_evidence: []
property:
  preconditions: []
  operation: []
  observation: {}
  oracle: {}
  environment: {}
  provenance: []
candidate:
  origin: evidence-derived-reference | public-system-output | repository-migration | researcher-mutant
  artifact_or_code:
  transformation_log: []
  residual_code: []
scope:
  valid_input_domain: []
  excluded_domain: []
  environment_id:
  probe_budget:
annotation:
  semantic_relation:
  evidence_state:
  diagnosis: []
  condition:
  confidence:
  unresolved_assumptions: []
review:
  primary_annotator:
  independent_reviewer:
  adjudication:
```

## 3. 两个正交标签轴

### 3.1 语义关系

- `identity-transport`：无需语义转换即可保持该性质；
- `adapted-transport`：通过明确、受限的输入/操作/观测/oracle/environment 转换可以保持；
- `divergent-by-design`：目标实现具有证据支持的合理不同设计；
- `library-unsupported`：目标库在声明版本和范围内没有对应能力；
- `relation-undetermined`：现有证据不足以判断库间关系。

### 3.2 候选证据状态

- `supported-within-scope`：在声明范围和预算内，义务均满足且未发现反例；
- `refuted`：存在满足前置条件、可重复执行并违反 oracle 的有效反例；
- `undetermined`：环境、证据、预算或表达能力不足，不能给出支持或否定。

`divergent-by-design`、`library-unsupported` 不是 `refuted` 的同义词。前者描述库间关系，后者描述具体候选在当前证据下的状态。

## 4. 诊断标签

诊断只解释状态，不替代状态：

- `invalid-mapping`：候选转换错误或遗漏；
- `precondition-mismatch`：候选在源性质有效域外运行；
- `oracle-mismatch`：观测或判定关系迁移错误；
- `design-divergence`：目标有证据支持的不同设计；
- `target-unsupported`：目标缺少该能力；
- `dsl-out-of-grammar`：当前 Candidate Mapping IR 无法表达，但不等于目标不支持；
- `environment-blocked`：版本、device、依赖或外部服务阻塞；
- `suspected-target-violation`：在合理关系已建立后，目标实现疑似违反自身规范；
- `insufficient-evidence`：证据不足。

若使用 `suspected-target-violation`，必须先排除错误映射、设计差异、目标不支持和环境噪声；在 maintainer 确认或 historical fix 前不得标为 confirmed bug。

## 5. 候选来源必须分层报告

- `evidence-derived-reference` 根据固定官方证据构造，用于建立有效候选和回归检查；不得与真实系统成功率混合。
- `researcher-mutant` 只用于校验 checker/probe 是否能识别已知语义风险；不得计为任何 baseline 的错误率。
- `public-system-output` 必须保存系统版本、模型、prompt、配置和原始输出；无法复现时标记 provenance limitation。
- `repository-migration` 必须锚定 issue、PR、commit 或测试迁移记录；维护者采纳不自动等于语义正确。

主结果分别报告三类候选，不允许混合分母。

## 6. 原子化规则

一条性质只能有一个主要 oracle。以下情况必须拆分：

- value、shape、dtype 同时被断言；
- 正常行为与异常行为同时出现；
- 前向值与梯度同时出现；
- 随机 replay 与分布性质同时出现；
- 同一参数化测试在不同条件下需要不同 adapter；
- 一条失败可能对应不同 clause 且无法唯一归因。

复合 oracle 仅在其组成项不可独立表达、且官方测试本身将其定义为单一 contract 时允许，并必须写明理由。

## 7. 证据规则

证据优先级：

1. 固定 commit 的源/目标官方测试与源码；
2. 官方规范或 API 文档；
3. historical issue/PR、修复提交和 maintainer 说明；
4. 独立动态探针；
5. 经独立复核的人工判断。

LLM、CoSMiT、IntentTester、KATRER 或其他被评估系统的输出只能作为候选，不能作为自身正确性的 ground truth。

## 8. 有效反例

反例必须同时满足：

- 满足源 property 的前置条件；
- 源、目标在冻结环境中均可执行，或目标失败本身就是预期诊断对象；
- 违反一个明确 oracle clause；
- 可由固定输入、版本和命令重复；
- 不是无效 API 调用、依赖缺失或随机噪声；
- 说明候选应被删除、修复，还是收紧 condition。

最小化反例时只删除与违反条款无关的输入维度、参数或执行步骤，不允许改变失败类别。

## 9. 条件精化

条件精化仅在以下要求全部满足时成立：

1. 条件来自可解释条款，例如 axis、dtype、shape、容差或版本；
2. 条件排除了已知反例；
3. 在保留子域内重新执行 checker；
4. 报告被排除输入比例和仍未覆盖的边界；
5. 不把 `dsl-out-of-grammar` 伪装为目标库限制。

条件精化输出仍是 `supported-within-scope`，不是全域证明。

## 10. 数据划分与冻结

- `development`：12 个 API groups，用于修订 Property IR、Candidate Mapping IR 和 probe policy；
- `evaluation-holdout`：3 个 API groups，在 IR/规则冻结前只公开 family 与证据入口，不公开具体原子条款；
- IR 冻结后生成 hash；任何因 holdout 失败产生的语法修改都必须作为新版本，并把原 holdout 结果保留为失败；
- 同一 API family 不跨 development/holdout，防止参数变体泄漏。

## 11. 主标注与分层独立复核

- 全量样本由 primary annotator 标注；初始状态为 `provisional-primary`；
- 独立复核基础样本固定为总样本的 20%–30%，当前 45-slot pilot 取 12 条，即 26.7%；
- 基础样本按 API group 和语义维度分层；
- 所有真实系统输出、repository migration、高风险诊断、primary/reviewer 分歧和 `suspected-target-violation` 强制复核，不受 30% 上限限制；
- reviewer 只能看到固定证据和候选代码，看不到 CoSMiT 状态、probe 结果、primary verdict 或建议 condition；
- 分歧按 property boundary、relation、state、diagnosis、condition 五类记录并仲裁。

完成独立复核或仲裁后才能标为 `reviewed-ground-truth`。未复核样本必须在结果表中单独标识。

## 12. 停止与排除规则

以下样本保留在 ledger，但不进入主效果分析：

- 源测试依赖不可固定的私有基础设施；
- 目标版本或对应实现不可获得；
- 无法定义主要 observation/oracle；
- 真值只能由被评估系统自身给出；
- 候选代码不完整且无法恢复执行；
- 运行成本超过预注册预算。

`dsl-out-of-grammar` 不自动排除：它属于 coverage 结果，必须计入分母。

## 13. 报告要求

每个比例必须报告分子、分母和置信区间。主结果至少分层展示：

- valid candidates 与 invalid candidates；
- researcher mutants、public system outputs、repository migrations；
- development 与 evaluation-holdout；
- supported、refuted、undetermined；
- 各 semantic dimension 与 diagnosis。

有限动态证据统一称为 scope-bounded support，不使用 formal proof/certification 表述。
