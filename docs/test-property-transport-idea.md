# CoSMiT 研究构想：跨实现测试性质迁移

> 状态：研究问题基线草案  
> 更新日期：2026-08-14  
> 用途：固定 CoSMiT 的核心研究对象、形式化定义、方法边界与可证伪条件。后续论文、实验和 PPT 应以本文为准；旧版“可迁移性预测 + 生成后认证”方案仅作为演化记录。

## 1. 研究定位

CoSMiT 不再被定义为既有测试迁移系统的后处理认证器，也不以“生成一个可编译、可执行的目标测试”为最终问题。其研究对象是：

> **跨实现测试性质迁移（Cross-Implementation Test Property Transport）**：给定源实现上的原子测试性质、目标实现、允许的语义适配代数以及输入与环境条件，自动合成保持该性质的跨实现迁移映射；若候选映射不成立，则生成可执行反例；若现有证据不足，则显式拒绝判定。

推荐论文定位：

> **Beyond Test Migration: Modeling and Solving Cross-Implementation Test Property Transport**

KATRER、IntentTester 和直接 LLM 翻译主要回答“如何生成或复用目标测试”。CoSMiT 回答的是更前置且独立的问题：“源测试中的哪项性质能够被带到目标实现、需要什么语义适配、适用边界是什么、什么输入能够否定该迁移假设”。因此，既有迁移系统是 CoSMiT 的下游消费者和实验基线，而不是 CoSMiT 必须依赖的输入端。

### 1.1 表示层研究空缺

IntentTester 已经提供 TDL、目标仓库语义对齐、Planning 和 Verification，因此 CoSMiT 不能声称现有方法“没有 IR”或“没有语义对齐”。真正的空缺是：TDL 将源测试压缩为以自然语言为主要载体的单边意图表示，它提高了跨语言和跨库可移植性，但不保证保留会改变合法迁移映射的全部语义证据。

设测试抽象器为 \(A\)，目标实现为 \(T\)。若存在两个源测试：

\[
A(t_1)=A(t_2)
\quad\land\quad
ValidAdapters(t_1,T)\neq ValidAdapters(t_2,T)
\]

则称该表示发生了 `transport-critical semantic collision`，即不同迁移契约被压缩为不可区分的意图。易被隐化或遗漏的信息包括精确输入域、dtype/shape、控制与状态依赖、观测位置、异常类型、数值容差、随机环境和源码来源。

CoSMiT 不声称构造绝对无损的 IR，而是构建在声明观测模型下 `evidence-preserving` 的 Property IR：自然语言用于解释、检索和候选生成；精确条款绑定源码、数据流和可执行验证义务；无法恢复的信息显式标记为 unresolved/unknown。

## 2. 基本对象

设：

- \(S_v\)：版本固定的源实现；
- \(T_v\)：版本固定的目标实现；
- \(E\)：运行环境，包括语言、依赖、硬件、后端和随机性配置；
- \(D\)：声明的输入域；
- \(\mathcal A\)：允许使用的语义适配器集合；
- \(B\)：动态探测、求解和验证预算；
- \(\Omega\)：允许观察的行为集合。

### 2.1 原子测试性质

测试代码首先被分解为原子性质：

\[
\kappa=\langle P, C, O, \phi, \Pi\rangle
\]

其中：

- \(P(x)\)：前置条件，如 shape、dtype、参数范围和设备约束；
- \(C(S,x)\)：源实现中的操作或调用序列；
- \(O\)：观测函数，如返回值、shape、dtype、异常、梯度、状态或分布；
- \(\phi\)：施加在观测结果上的 oracle 或关系性质；
- \(\Pi\)：来源信息，包括测试位置、提交、issue/PR 和适用版本。

“测试代码”只是性质的一种可执行实现。CoSMiT 迁移的是 \(\kappa\)，不是源代码字符串或整段自然语言描述。

### 2.2 迁移映射

一个迁移映射定义为：

\[
\mu=\langle
\mu_{in},
\mu_{op},
\mu_{obs},
\mu_{oracle},
\mu_{env}
\rangle
\]

分别表示输入、操作、观测、oracle 和环境的映射。映射可以是恒等映射，也可以包含参数重命名、布局转换、dtype 转换、单操作到组合操作、异常抽象或容差关系。

### 2.3 性质迁移成立条件

对于声明输入域 \(D\)，若存在 \(\mu\in\mathcal A\)，使：

\[
\forall x\in D,\quad
P(x) \Rightarrow
R_\kappa\left(
O(C(S_v,x)),
\mu_{obs}(O(C(T_v,\mu_{in}(x))))
\right)
\]

则称 \(\kappa\) 在 \((S_v,T_v,E,D,\mathcal A)\) 条件下可迁移。\(R_\kappa\) 是性质相关关系，可以是：

- 精确相等或容差相等；
- shape、dtype 或布局关系；
- 异常类型和错误条件对应；
- 梯度或高阶梯度关系；
- 状态变化、副作用或随机性关系；
- 集合、排序、单调性、幂等性等蜕变关系；
- 统计或分布关系。

因此，跨实现迁移不等同于逐值相等，也不等同于目标测试执行通过。

## 3. 三个必须分离的判定问题

### P1：性质可迁移性

判断是否存在 \(\mu\in\mathcal A\) 保持给定性质。它回答“目标实现中是否存在该源性质的合理对应物”。

### P2：迁移映射合成

在允许的适配代数中合成具体 \(\mu\)，并给出各条款的条件和证据。它回答“输入、操作、观测和 oracle 应如何转换”。

### P3：目标实现符合性

在迁移映射已经独立成立后，判断目标实现是否满足 \(\mu(\kappa)\)。只有当迁移映射有效而目标违反该性质时，结果才是目标缺陷候选。

该分解避免将以下现象混为一个“测试失败”：

1. 生成器错误实现了映射；
2. 源目标存在合理的设计差异；
3. 目标根本不支持对应能力；
4. 目标实现违反了一个合法迁移的性质。

## 4. 输出模型

CoSMiT 的结果同时包含“语义关系”和“证据状态”，二者不得压缩成一个标签。

### 4.1 语义关系

- `identity-transport`：恒等或仅语法级映射即可保持性质；
- `adapted-transport`：需要合法语义适配后保持性质；
- `divergent-by-design`：目标存在明确且合理的不同语义；
- `unsupported`：目标在声明能力范围内没有对应行为。

### 4.2 证据状态

- `formally-certified`：通过符号证明或完整有限域穷举得到支持；
- `bounded-supported`：在声明输入域、环境和验证预算内未找到反例；
- `refuted`：存在能够违反候选迁移假设的有效反例；
- `undetermined`：当前证据或预算不足，拒绝作出强结论。

`undetermined` 是认识状态，不是不可迁移类别。`identity-transport` 和 `adapted-transport` 是合成结果，不应被预先当作分类标签。

### 4.3 迁移结果记录

每个结果至少保存：

```yaml
property_id: string
source: {library, version, api, test_location}
target: {library, version, api_or_composition}
preconditions: []
clauses: []
adapter:
  input: []
  operation: []
  observation: []
  oracle: []
  environment: []
semantic_relation: identity-transport | adapted-transport | divergent-by-design | unsupported
evidence_state: formally-certified | bounded-supported | refuted | undetermined
evidence: []
counterexamples: []
residual_risks: []
budget_and_scope: {}
```

“认证”是该结果中的一种证据状态，不是 CoSMiT 的问题定义。

## 5. 反例与条件收紧

反例定义为：

\[
c=\langle x,e,\mu,\kappa_j,trace\rangle
\]

它表示在环境 \(e\) 和输入 \(x\) 下，候选映射 \(\mu\) 违反了原子条款 \(\kappa_j\)。反例应指向被否定的具体假设，而不只是保存一条失败日志。

反例产生后，系统可以：

1. 收紧输入域或前置条件；
2. 修改输入、操作、观测或 oracle 适配；
3. 将该差异归为设计差异或目标不支持；
4. 在当前适配代数和预算下拒绝迁移；
5. 若迁移映射已独立成立，则生成目标缺陷候选。

核心求解过程采用反例引导的迭代形式：

\[
\text{提出候选映射}
\rightarrow
\text{生成验证义务}
\rightarrow
\text{搜索反例}
\rightarrow
\text{修正映射或条件}
\]

不声称“绝对不可迁移”。所有结论均相对于版本、环境、输入域、观测模型、适配代数和验证预算：

\[
\mathcal T(\kappa,S_v,T_v,E,D,\Omega,\mathcal A,B)
\]

### 5.1 反例作为候选空间剪枝

设当前剩余 adapter version space 为：

\[
V_i=\{\mu\in\mathcal A\mid\forall c\in C_i, Preserve(\mu,c)\}
\]

新反例不仅否定当前候选，还应淘汰所有违反同一条款约束的 adapter。普通 CEGIS 返回任意反例，只保证删除当前错误候选；CoSMiT 进一步主动选择能够最大化候选行为分歧的输入，并把具体失败泛化为 clause-level no-good constraint。

候选输入的效用定义为：

\[
Utility(x)=
\frac{ExpectedVersionSpaceReduction(x)}{ExecutionCost(x)}
\]

因此反例同时承担两项职责：作为迁移假设的可执行否定证据，以及作为高成本跨库执行中的搜索控制信号。效率必须用候选淘汰率、verifier/执行次数、总时间和 false-pruning rate 共同验证，不能只比较反例数量。

## 6. 适配代数的首版范围

首版适配语言优先覆盖深度学习和数值计算库中的高频语义差异：

- 参数重命名、重排和默认值显式化；
- axis/dim、layout 和 shape 的置换、扩展、压缩；
- scalar/tensor lifting 和容器转换；
- dtype cast、类型提升和数值精度条件；
- device、backend、seed 和随机状态映射；
- 单 API 与 API 组合之间的操作映射；
- 输出投影、重排、归一化和状态提取；
- 精确、近似、异常、梯度、蜕变和分布型 oracle；
- 测试框架 fixture 与资源环境适配。

适配代数必须是受限、可记录和可执行的。若允许任意程序重写，“是否存在迁移”将失去可判定边界和解释价值。

## 7. 方法构想

CoSMiT 的核心不是 LLM 二分类器，而是一个“提议—约束—反例—精化”的混合求解器：

1. **性质原子化**：从源测试提取前置条件、操作、观测和 oracle；
2. **候选关系检索**：利用签名、文档、源码、调用和已有测试提出目标对应物；
3. **映射提议**：在适配代数中生成候选 \(\mu\)；
4. **验证义务生成**：按性质条款构造静态约束和动态探针；
5. **反例搜索**：使用边界生成、约束求解、差分执行和 counterfactual mutants 寻找反例；
6. **条件精化**：根据反例修改映射、收紧条件或拒绝判定；
7. **目标实现生成**：将已求解的 \(\mu(\kappa)\) 交给任意迁移系统生成原生测试；
8. **目标符合性判断**：独立区分生成错误、设计差异和目标缺陷。

LLM 可用于性质和映射的候选生成、文档证据检索以及反例解释，但不能仅以自然语言自评产生最终语义结论。

## 8. 与 KATRER、IntentTester 的关系

| 系统/方向 | 主要输入 | 主要任务 | 主要判据 | CoSMiT 的角色 |
| --- | --- | --- | --- | --- |
| KATRER | 源测试、代码与知识图 | 知识感知测试复用与重构 | 可执行性、通过率、功能一致性判断 | 提供独立性质映射和反例；评估复用结果是否实现正确性质 |
| IntentTester | 源测试意图描述、仓库上下文 | 意图驱动跨库测试生成 | 语法、执行、意图相关验证 | 将自然语言 intent 精化为可执行条款与适配义务 |
| Binary Adapter Synthesis | reference/target functions、有限 adapter family | 用 CEGIS 合成输入/输出 adapter 并判断函数可替代性 | 返回 adapter、反例或 family 内无解 | 最直接的方法先例；CoSMiT 扩展到局部条件化测试性质、丰富 oracle、条件学习与错误归因 |
| 直接 LLM 迁移 | 源代码和提示 | 代码翻译/生成 | 编译、执行或 LLM 自评 | 作为无显式性质模型的弱基线 |
| CoSMiT | 原子性质、源目标实现、适配代数 | 合成或否定性质迁移 | 条款保持、有效反例、条件化证据 | 生成器无关的迁移知识求解层 |

关键区别可写为：

\[
\text{KATRER/IntentTester}:\quad
Generate(t_t\mid t_s,context)
\]

\[
\text{CoSMiT}:\quad
SynthesizeOrRefute(\mu\mid\kappa,S,T,\mathcal A)
\]

## 9. 预期贡献

1. **问题与模型**：实证刻画自然语言 intent 的迁移关键语义损失，定义跨实现测试性质迁移，并区分性质可迁移性、映射实现和目标符合性；
2. **适配与求解**：提出面向数值/DL 库的可执行适配代数，以及反例引导的映射合成方法；
3. **Benchmark**：构建包含恒等迁移、适配迁移、设计差异、目标不支持和未确定样本的原子性质数据集，并保存金标准映射与反例；
4. **实证价值**：证明求解出的迁移知识可以改善多个生成系统，并通过历史缺陷、mutation 和真实 issue/PR 验证维护价值。

形式化符号本身不足以构成贡献。投稿成立依赖于领域适配代数、可工作的求解算法、独立金标准和跨生成器实证结果。

## 10. 可证伪条件

以下结果将削弱或否定核心构想：

- 原子性质无法被稳定标注，或不同评审者无法对映射条款达成一致；
- 适配代数只能覆盖少量简单参数改名，无法表达真实语义差异；
- 候选映射的正确性主要由具体 LLM 或 prompt 决定，约束与反例没有独立增益；
- 高精度只能通过对绝大多数性质输出 `undetermined` 获得；
- 反例无法可靠区分错误映射、设计差异和目标缺陷；
- 对 KATRER、IntentTester-style 和直接 LLM 生成均无稳定下游收益；
- 新方法只提升执行率，未提升条款保持、mutation 或历史/真实缺陷证据。

## 11. 当前决策与待解决问题

当前决策：以“合成或反驳跨实现测试性质迁移”为 CoSMiT 的主问题；将“可迁移性概率”降为搜索排序信号，将“迁移认证”降为输出证据，将测试代码生成降为下游实现阶段。

首轮尚需验证：

1. 什么粒度的性质既可标注又具有维护意义；
2. 适配代数的最小完备子集是什么；
3. “设计差异”应由文档、实现、开发者测试还是维护者意见共同决定；
4. 如何构造与生成器输出独立的金标准映射和反例；
5. 哪些样本能够 `formally-certified`，哪些只能表述为 `bounded-supported`；
6. 如何设计对 KATRER 和 IntentTester 公平、可复现且不依赖其内部代码的比较。
