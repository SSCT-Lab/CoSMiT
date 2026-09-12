# CoSMiT Feasibility Annotation Guide v0.1

> 状态：试标注版本；完成首批 10 条后修订。  
> 目标：建立跨实现测试性质、条件化 adapter 与反例的独立真值，不评价生成代码的表面相似度。

## 1. 标注单位

基本单位是原子测试性质：

\[
\kappa=\langle P,C,O,\phi,E,\Pi\rangle
\]

一条记录只允许包含一个主要 oracle。若同一测试同时断言 value、shape、dtype 和 exception，应拆成多条 property，并用 `parent_test_id` 关联。

## 2. 必填字段

```yaml
property_id:
group_id:
parent_test_id:
source:
  library:
  version:
  repository:
  commit:
  test_path:
  test_name:
  source_url:
target:
  library:
  version:
  candidate_api_or_composition:
property:
  preconditions: []
  operation: []
  observation:
  oracle:
    type:
    parameters: {}
  environment: {}
  provenance: []
gold_adapter:
  input: []
  operation: []
  observation: []
  oracle: []
  environment: []
valid_domain: []
excluded_domain: []
semantic_relation:
evidence_state:
gold_counterexamples: []
unresolved_assumptions: []
annotator:
reviewer:
adjudication:
```

## 3. 原子化规则

一条 property 必须满足：

- 只有一个主要观测点；
- 只有一个可独立判定的 oracle；
- 前置条件可写成具体值、集合或谓词；
- 源端操作和观测之间的数据流可追踪；
- 删除该 property 后，原测试至少失去一种可描述的缺陷检测能力。

以下情况必须拆分：

- 同时检查返回值和 dtype；
- 同时检查正常输入和异常输入；
- 同时检查前向值和梯度；
- 同时检查确定性和分布性质；
- 同一参数化测试实例具有不同 adapter 条件。

## 4. 五类 Adapter

- `input`：参数重排、axis/dim、shape/layout、scalar/tensor、dtype 或容器转换；
- `operation`：API 替换、单操作到组合操作、显式默认值和调用序列；
- `observation`：返回值投影、tuple/dict 解包、状态或异常捕获位置；
- `oracle`：exact/approx、容差、异常对应、梯度、蜕变或统计关系；
- `environment`：版本、device/backend、seed、determinism 和 fixture。

若 gold adapter 需要任意代码生成才能描述，标记 `dsl_gap`，不得用自由文本伪装成已覆盖。

## 5. 语义关系与证据状态

语义关系：

- `identity-transport`：仅语法替换或恒等映射；
- `adapted-transport`：需要至少一个语义 adapter；
- `divergent-by-design`：目标行为有明确、合理且有证据的不同设计；
- `unsupported`：目标没有对应能力。

证据状态：

- `formally-certified`：符号证明或完整有限域穷举；
- `bounded-supported`：声明范围和预算内未找到反例；
- `refuted`：存在有效反例；
- `undetermined`：证据不足、冲突或预算耗尽。

不得把有限随机测试通过标为 `formally-certified`，也不得把 `undetermined` 写成 `unsupported`。

## 6. Gold 证据优先级

1. 源/目标仓库已有 counterpart tests；
2. 官方文档或规范；
3. 固定版本源码和独立动态探针；
4. historical issue/PR、修复提交或 maintainer 说明；
5. 双人独立标注后的仲裁结论。

LLM、CoSMiT、IntentTester 或 KATRER 的输出只能作为候选，不能作为 gold 证据。

## 7. 有效反例标准

反例记录至少包含：

```yaml
input:
environment:
candidate_adapter:
violated_clause:
source_trace:
target_trace:
expected_relation:
observed_violation:
reproducibility:
```

反例必须：

- 满足源 property 的前置条件；
- 在固定环境中可复现；
- 指向 adapter 或某一条款，而不是基础设施错误；
- 排除错误 API 使用、无效输入和非确定性噪声；
- 能说明应删除候选、修改 adapter，还是收紧 valid domain。

## 8. Transport-critical loss 判定

对 TDL-style intent、普通 LLM summary、TDL + AST facts 分别检查 input domain、dtype/type promotion、shape/layout、defaults、state/seed、observation point、oracle type/parameters、exception、environment/version 和 provenance。

只有同时满足以下条件才记为 `transport-critical`：

1. 表示遗漏、模糊化或合并了某条款；
2. 该条款变化会改变合法 adapter、valid domain、semantic relation 或 evidence state；
3. 变化能够由源码证据或动态探针验证。

## 9. Semantic Collision 判定

候选 pair 需要分别回答：

1. 两条表示是否相同，或在预定义相似标准下不可区分？
2. 两条源 property 是否只在一个迁移关键条款上不同？
3. 它们的合法 adapter 集或适用条件是否不同？
4. 是否存在可执行输入区分两者？

结果标签：

- `confirmed`；
- `rejected-representation-distinguishes`；
- `rejected-same-adapter-set`；
- `undetermined`。

## 10. 双人标注协议

- 标注者 A、B 独立阅读相同源证据；
- 两人不得查看 CoSMiT 或基线输出；
- 首轮独立填写 property 和 gold adapter；
- 比较原子边界、五类 adapter、valid domain 和 semantic relation；
- 分歧由第三人依据证据仲裁；
- feasibility 阶段先记录 exact agreement 和分歧类型，样本充分后再决定是否报告 Cohen's kappa 等统计量。

## 11. 排除规则

以下样本不进入主分析，但保留在 exclusion ledger：

- 源测试依赖无法固定的私有基础设施；
- 目标实现或对应版本不可获得；
- 行为依赖不可控外部服务；
- 无法确定主要 oracle；
- 需要超出当前 DSL 范围的任意程序重写；
- 只有命名差异且不能检验表示损失或非平凡 adapter；
- 真值只能由被评估系统自身提供。

## 12. v0.1 修订触发条件

完成第一批 10 条后，集中修订：字段歧义、原子化困难、DSL gap、`divergent-by-design` 与 `unsupported` 的边界、动态探针稳定性，以及 collision 的表示等价标准。

## 13. 首批 10 条后的 Pilot Addendum（2026-08-31）

以下规则由首批 seed properties 强制加入，后续 v0.2 应正式合并：

- **区分官方测试与 counterfactual**：真实测试变体必须标记 `source-official-test-plus-counterfactual`，并说明只改变了哪个因素；不得伪装成仓库中原有测试。
- **区分 provisional 与 Gold**：单人完成的 property 只能标记 `provisional-single-annotator`；经过 B 独立复核和仲裁后才可升级为 Gold。
- **记录表示生成方式**：手工 TDL proxy、LLM summary、实际 IntentTester TDL 和 AST facts 必须使用不同标签，禁止把 proxy 结果归因给基线系统。
- **错误候选不等于 baseline**：为寻找反例而人工注入的 naive adapter 只能用于验证性质和探针，不能计为任一迁移方法的错误率。
- **优先保存可执行但错误的 witness**：若错误 adapter 既能构建又能执行，应优先保留其数值/语义偏差，而不只保存更容易发现的 shape exception。
- **Gold adapter 必须声明边界**：每条 adapted transport 必须同时记录 valid domain、excluded domain 和 unresolved assumptions；单个 witness 不得外推为全域成立。
- **关系型 oracle 不做逐值迁移**：随机性、分布和状态测试优先迁移 replay、分布或状态关系，除非有规范明确要求跨实现比特级一致。
- **隐式 contract 单独标注**：dtype promotion、类别轴、tie policy、非单例行为和梯度 materialization 即使未作为字面参数出现，也必须作为显式条款进入 Property IR。
