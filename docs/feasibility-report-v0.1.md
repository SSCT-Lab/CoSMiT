# CoSMiT Feasibility Study v0.1

> 执行日期：2026-08-31  
> 方向：PyTorch 2.9.1 → TensorFlow 2.20.0  
> 环境：Python 3.10.9，macOS 15.7.7 arm64，CPU  
> 结论等级：feasibility evidence；不能作为正式基线效果或普遍性结论。

## 1. 本轮回答的问题

本轮不评估完整 CoSMiT，而回答三个前置问题：

1. 真实官方测试是否能够被拆成可追溯的原子测试性质？
2. 非平凡跨实现差异能否用 input、operation、observation、oracle、environment 五类 adapter 表达？
3. 是否能构造自然语言目标相同、但合法 adapter 集不同的可执行样例？

## 2. 数据和证据

- 10 个 API group；
- 10 条 provisional seed properties；
- 20 条固定 commit 的 PyTorch/TensorFlow 官方测试证据；
- 1 个统一动态探针 runner；
- 10 组错误候选与条件化正确 adapter；
- 13 个 transport-critical clauses；
- 3 个 collision records，其中 2 个用于最低验收。

数据文件：

- `benchmark/feasibility/properties.yaml`
- `benchmark/feasibility/evidence.yaml`
- `benchmark/feasibility/representations.yaml`
- `benchmark/feasibility/collisions.yaml`
- `benchmark/feasibility/dynamic-trace.json`
- `benchmark/feasibility/run_seed_probes.py`

全部性质均为 `bounded-supported`，没有性质被标记为 `formally-certified`。当前 annotations 只有 provisional annotator A，不能称为最终 Gold Standard。

## 3. Seed Property 结果

| ID | 迁移关键差异 | 正确 adapter | 错误候选反例 |
| --- | --- | --- | --- |
| PTF-001 | 整数 sum 输出 dtype | 目标输入先 cast 到 int64 | 值相同但目标输出仍是 int32 |
| PTF-002 | 整数 mean 的截断行为 | 归约前 cast 到 float32 | 1.5 被目标整数 mean 截断为 1 |
| PTF-003 | argmax 输出 dtype | 显式 output_type=int64 | int32 结果违反 dtype 条款 |
| PTF-004 | 两维交换与完整 perm | 构造 identity perm 后交换两维 | 省略 perm 会反转全部维度 |
| PTF-005 | 非单例 squeeze 行为 | 条件化 squeeze-or-identity | 直接 tf.squeeze 抛出异常 |
| PTF-006 | 只有下界的 clamp | 映射到 tf.maximum | 虚构有限上界会错误截断合法大值 |
| PTF-007 | 近似 oracle 参数 | 精确保留 rtol/atol | 目标默认容差改变通过/失败结果 |
| PTF-008 | 交叉熵类别轴与 reduction | 类别轴移到末尾后 sparse CE + mean | 错误映射可能执行成功但计算错误损失 |
| PTF-009 | 随机性观测关系 | 比较目标内部 seed replay | 跨库逐值相等不成立，但两边 replay 均成立 |
| PTF-010 | 未连接梯度策略 | unconnected_gradients=ZERO | 目标默认返回 None 而非数值零 |

在单个声明 witness 上，10 个 adapted candidates 均保持性质，10 个对应 naive candidates 均被反例否定。该结果只说明样本、adapter schema 和探针能够形成闭环；错误候选是按已知风险有目的构造的，不能解释为任何现有迁移系统的失败率。

语义关系分布为 9 个 `adapted-transport`、1 个 `identity-transport`。当前选择明显偏向非平凡正例，尚未覆盖足够的 `divergent-by-design` 和 `unsupported`。

## 4. 表示层初步审计

| 表示 | 保留的关键条款 | 保持率 |
| --- | ---: | ---: |
| unrestricted summary proxy | 1 / 13 | 7.7% |
| TDL-style proxy | 7 / 13 | 53.8% |
| TDL + AST facts proxy | 10 / 13 | 76.9% |
| provisional Property IR | 13 / 13 | 100% |

主要损失来自：隐式 dtype promotion、tie policy、非单例 squeeze 行为、精确容差、类别轴契约和梯度 materialization。

这些数字不能写进论文结果部分，原因是 TDL-style 尚未通过 IntentTester 的官方 pipeline 生成，普通 summary 也不是盲态重复实验。当前结果只能支持两个设计判断：

1. 仅保留高层目标的意图表示在构造上不是 transport-sufficient；
2. AST facts 能补回显式字面量，但仍不能自动恢复隐式 API contract。

正式 RQ1 必须运行官方 IntentTester-style 表示、固定模型与 prompt，并由盲态标注者判断条款保持。

## 5. Semantic Collision

已确认两个 `goal_only_intent` abstraction 下的 collision：

1. **值相等与值 + dtype 相等**：两条性质都可表述为“对整数张量求和并检查结果”，但直接 `tf.reduce_sum` 只属于 value-only property 的合法 adapter 集。
2. **不同近似容差**：两条性质都可表述为“检查两个浮点值接近”，但 `atol=1e-5` 与 `atol=1e-6` 需要不同 oracle adapter；差值 `5e-6` 可执行地区分两者。

另一个 squeeze pair 在 goal-only abstraction 下发生 collision，但加入 AST shape facts 后即可区分。这说明论文不能声称“所有自然语言都必然有损”，而应研究具体表示在何种条款和抽象级别下不充分。

实际 IntentTester TDL 的 collision 数仍为 0 confirmed / 3 undetermined，因为本轮没有执行其正式抽取流程。

## 6. Motivating Case：可执行但错误的 Cross-Entropy 迁移

源性质来自 PyTorch cross-entropy 官方测试族。PyTorch 的高维 logits 使用 `[N, C, ...]`，类别轴为 1；TensorFlow sparse softmax cross entropy 将最后一维解释为类别。高层 intent 都可以写成：

> Compute sparse cross-entropy for logits and class-index labels, then compare the mean loss.

朴素映射直接把相同 logits 和 labels 交给 TensorFlow。当 logits shape 为 `[2, 3, 3]` 时，shape 恰好兼容，因此目标代码能够正常执行，但它沿错误类别轴计算：

| 执行 | mean loss |
| --- | ---: |
| PyTorch source | 0.2113235146 |
| TensorFlow naive mapping | 1.2837294340 |
| TensorFlow adapted mapping | 0.2113234997 |

错误映射相对源结果的绝对误差为 `1.0724059194`；将 logits 从 `[N, C, L]` 转为 `[N, L, C]` 后，误差降为 `1.49e-8`。

该案例体现论文核心动机：编译和执行成功不能证明测试性质迁移正确；类别轴是 transport-critical clause，必须进入可执行 Property IR 和 adapter obligation。

## 7. Gate A 判断

| 条件 | 结果 | 说明 |
| --- | --- | --- |
| 原子性质可以标注 | 部分通过 | 10 条均能形成记录，但只有单人 provisional annotation |
| adapter 可以受限表达 | 通过 feasibility | 10 条均可表达；squeeze 要求条件 guard |
| 存在迁移关键信息损失 | 部分通过 | goal-only abstraction 已确认；官方 IntentTester TDL 未验证 |
| 存在可执行反例 | 通过 feasibility | 10 个错误候选均有 witness |
| 标注一致性可接受 | 未完成 | 缺独立 annotator B 和仲裁 |

因此 Gate A 当前状态为 **partial pass**。可以进入 Property IR/Adapter DSL 的原型设计，但不能冻结 RQ1 结论或启动大规模 benchmark。

## 8. 下一阶段必须完成

1. 由独立 annotator B 复核 10 条 property、adapter、valid domain 和关系标签；
2. 运行真实 IntentTester/TDL-style extraction，而不是继续使用手工 proxy；
3. 将每组扩展到 3–5 条性质，补齐 30–50 条 feasibility 数据；
4. 加入 `divergent-by-design`、`unsupported` 和 `undetermined`，降低正例选择偏差；
5. 冻结最小 Adapter DSL，尤其是 condition guard、axis permutation、oracle tolerance 和 observation relation；
6. 对 cross-entropy motivating case 补充 repository issue/PR 或历史修复证据。

