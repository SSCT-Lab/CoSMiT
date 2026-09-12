# CoSMiT 既有结果审计与阻塞清单

日期：2026-09-08。范围：本地候选、响应、检查代码、数据索引、论文草稿与执行计划。此次未重新调用模型、未执行 CuPy 候选、未重新运行全部历史动态 witness；原始实验结果保留不变。本文件是结论纠偏与阻塞清单，不是已完成实验的性能报告。

## 结论

已有材料可以支撑动机和小规模可行性，但不能支撑“完整复现 KATRER”“自动认证已经有效”或“反例搜索优于 baseline”。最需要撤回的是 KATRER-NC-001 的正向支持判定：旧检查器只识别语法特征和源码字符串，没有完成候选行为验证。三条 KATRER 改编版候选的当前性质证据状态均应读作 `undetermined`，不是已证错，也不是已证成立。

项目不需要推倒重来，但下一步应先补方法与判定可信度，再扩批量生成。

## 1. 哪些结果可以保留

| 材料 | 已有证据 | 不能由此推出 |
| --- | --- | --- |
| 13 条 provisional 性质、26 个 reference/mutant cases | pilot schema 校验通过；历史记录含针对已知风险的动态 witness | 自动发现能力、100% 检出率、总体覆盖率 |
| IntentTester 5,531 个公开候选索引 | 本轮逐文件哈希校验通过，54 条 review sample 可对齐 | 5,531 条已完成性质检验，或完整执行了生成流水线 |
| simplejson 方向 680 条，659 条 Python 语法有效 | 静态扫描记录中 0/659 显式导入 simplejson，626 条导入 stdlib json | 659 条都是语义错误；静态未发现等于动态绝不调用 |
| 40 条 IntentTester 执行样本 | 历史结果 29 pass、8 测试期失败、3 import error | 29 条正确迁移；该定向样本代表所有库方向 |
| 4 条 source-backed qualification | 历史独立 reference 均满足所选性质，3 条候选自测通过但使用 stdlib json；标签仍 provisional | 已完成独立人工 ground truth 或真实新缺陷发现 |
| 3 条 KATRER 改编版候选 | 本轮代码、generation prompt、原始生成文本提取结果与摘要哈希全部一致；最终 generation/judge 均以 stop 结束，judge 均为 consistent | 官方端到端 KATRER 复现；独立 ground truth；目标运行通过 |

“independent reference”指与候选分开构造的参考测试，不等于第二位研究者独立复核。13 条性质的 reference 与 mutant 也不是 26 个统计独立样本。

## 2. 已实证确认的检查器问题

证据：[诊断脚本](../benchmark/public_systems/audit_katrer_results.py)、[冻结输出](../benchmark/public_systems/katrer-audit-2026-09-08.json)。脚本仅解析代码，不执行构造样例、不访问模型。

构造了四个应拒绝的条款保持主张，旧检查器全部返回 true：

| 构造样例 | 实际问题 | 旧结果 |
| --- | --- | --- |
| 导入 CuPy，但在 raises 内调用 NumPy FFT | 目标操作未绑定 | clause preserved + target binding observed |
| 在 CuPy FFT 前主动 raise ValueError | 目标 FFT 不可达，异常来自别处 | clause preserved |
| 将三个边界调用放入 if False | 没有执行任何边界检验 | clause preserved |
| 死代码中堆积 squeeze/reshape，使用 ndim != 0，不写有效断言 | 操作计数不等于性质保持，比较方向也错误 | clause preserved |

这四个是检查器的 researcher-constructed negative controls，不能算成 KATRER 的四个错误，也不能据此断言三条真实候选错误。

原因集中在 [katrer_property_check.py](../benchmark/public_systems/katrer_property_check.py)：callee 后缀匹配不解析导入绑定；AST 遍历忽略可达性和数据流；squeeze 检查不验证断言和比较运算符；按 case ID 注册特例，不能说明通用 Property IR checker 已实现。

`target_static_evidence` 仅检查整个文件中出现函数名或字符串。它没有证明候选走到相应分支、异常来自目标操作、输入满足前置条件。`main` 又为 NC-001 特设正向判定。因此旧 `supported-within-static-source-scope` 缺少可审计的推导，应暂停使用。

另两个信号需要改名而非误当认证：空文本被 `syntax_status` 判为 valid 是合法的 Python 语法事实，但不是有效测试；只有 `import cupy` 就被标为 `target_operation_binding=observed`，实际只证明 import 出现。

## 3. KATRER 复现范围比此前叙述更窄

[输入清单](../benchmark/public_systems/katrer-reproduction-inputs.yaml) 已正确标记 `KATRER-reproduction-variant`，但叙述仍容易让人理解为只换了 API endpoint。实际偏差包括：

- source/target API 对由清单手工指定，不是上游图谱检索产生。
- TestIntention 字段由函数上下文拼接，不是完整 Test Fingerprint 流水线输出；KG、检索中间结果和 API Verification 角色没有跑通。
- runner 重建 generation/judge prompt，未完整实现论文的语义不一致后重新生成、API 验证反馈和轻量修复流程。传输失败重试不等于方法中的 refinement。
- 函数定义被压缩并截断到 1,500 字符。本轮确认 numpy.fft.fft、irfft、hfft 和 numpy.reshape 的片段在实现体之前已被截断。这是实质性的输入差异，不是单纯环境适配。
- 上游 QueryAns 缺失 Check 依赖，主入口不调用候选生成函数；这些缺口仍未因 wrapper 跑通而消失。

当前建议名称：**KATRER-inspired generation/judgement pilot（手工 API 对、改编提示词）**。历史 producer 字段不改，展示和汇总时必须带上述限定。完整官方 baseline 仍未复现。

论文使用 DeepSeek-R1；接口请求 ID 为 DeepSeek-R1，返回 model 为 deepseek-r1。可以称“同名模型接口”，不能仅凭模型名保证网关 checkpoint、部署版本和论文完全一致。当前 max_tokens=4096 也是需要披露的本地配置。实际仅运行 generation/judge 两种角色，不能说三个角色均已复现。

三个 checkout HEAD 本轮均与 manifest 一致。但 source 实际回放环境记录为 NumPy **2.1.3**，清单指定与 prompt 读取的是 **2.3.0** 源码。二者不一致，历史 source pass 不能冒充 2.3.0 复现。CuPy 候选动态执行记录为 **0/3**；本轮没有复查远端 GPU 是否恢复。

NC-002 包含多个边界调用，NC-003 包含值、shape、维度和类型等多个检查。三条测试不等于三条原子性质；NC-003 将 list 输入转成 cp.array 的适配也应登记。顺带确认：固定 CuPy 13.5.1 的 cp.complex_ 别名确实存在，不应误判为 API 不存在。

## 4. 论文定义与实验设计仍需收紧

### 正向证据门槛未封闭

草稿 §3.5 将“所有生成的 obligations 通过且预算内没有反例”作为 supported 条件，但没有定义 obligations 完整性、最低覆盖或成功测试数量。生成零条义务也可能真空通过；同一条 passing witness 不能支撑整个声明域。

建议区分声明域 D 与实际测试集合 X，以及 `evidence_kind`。动态结果只能明确声称“在 X 和固定环境下未发现违反”，并披露预算、有效探针数、覆盖和未决条款。有限域穷举或健全符号证明另行标注；缺必要条款、测试未收集、全部 skip 或环境失败不得支持。该修改建议尚未写入论文正文。

### 关系 R 的来源与候选执行接口需要定义

草稿写作 m(T,x)，但当前模型产物是含硬编码输入的 pytest 函数。需要明确如何提取输入插槽、注入新 x、保持 setup/oracle、采集观察值；否则 probe search 无法作用于真实候选，容易退化为研究者另写一个目标程序再测。

Rκ 必须来自候选之外的源性质及可核验适配依据，不能从候选输出反推。随机性、容差与梯度也不一定适用简单逐值相等。输入/观察/oracle adapter 应显式进入执行语义；未知关系保持未决。候选测试本身仍须保留，用于单独测量原有测试是否漏检。

### 已知 witness 不等于自动搜索结果

当前 seed/pilot 脚本是逐性质的固定 probe；没有共同候选集、等预算 probe policies、多 seed 与 held-out 结果。RQ2 的“按解释分歧/成本选择探针”仍是设计目标。不能把“我们能手工给反例”替换为“系统会高效找到反例”。

这也是贡献强度的主要风险：如果最终只有 IR 字段、case-specific 检查和手工 witness，仍会落回用户之前担心的 incremental 后处理。需要证明可复用的条款义务构建或探针选择机制，在未见 API family、真实候选上带来可测收益；不是继续增加术语或案例数量。

### 真实样本尚未支撑核心语义收益

IntentTester 的当前亮点主要是目标库绕过。这能证明 execute-only 不够，但简单 binding baseline 也可能发现。主实验必须再显示：**目标库确实被调用、原测试能通过，但仍丢失独立语义条款**，并比较 CoSMiT 超过 target-binding 检查的增量发现。

候选来源跨 PyTorch→TensorFlow、Java JSON→simplejson、NumPy→CuPy，不能把混合样本汇成一个无分层总分。同一 API family 下多个 mutant/条款存在相关性；未来置信区间应按合理 group 聚类处理，probe 重复次数不能膨胀样本量。40 条定向样本的 29/40 只能作为该样本自测结果，不能推出总体性能。

### 精化可能只是在删掉困难输入

条件接受标准仍是草稿占位符。要限制条件语法和复杂度、最低保留域、独立验证输入，并测试边界与域外样本。声明 precision/recall 时必须有独立的条件参照或明确评估分布，不能用发现条件的同一批探针给自己打分。

## 5. 工程记录与当前可重复性

- 六个最终模型响应均为 stop，但历史还保留两份无 finish_reason 的提前关闭 judge 响应；只计最终六份有效输出，不能把重试当独立样本。
- 当前 runner 只拒绝 finish_reason=None，未专门拒绝 length 等截断状态。此缺陷未影响本次核对的最终六份响应，但会污染后续批处理。
- 保存的是 SSE 拼接后的响应，不是完整逐事件原始流；失败尝试、请求 ID、全部费用及调用过程未形成统一账本。最终 judge 耗时不包含之前跨 run 的失败成本，不能作为端到端效率结果。
- 摘要缺少历史 runner 源码版本和各上下文文件哈希；本轮新审计哈希不能倒推证明 9 月 4 日运行时的代码版本。仍应补每次 run 的完整 provenance。
- TestRefactoringRes 当前有 10,133 个 .py；总文件数含元数据及新生成 pyc，不能以此前 10,137 个总文件当测试数量，更不能当成功迁移数量。
- task_plan、9 月 4 日报告与 reproduction-status 存在时间截面差异。本轮补审计入口；保留旧记录，不让读者把“当时暂无候选”误读为当前状态。

本轮运行：`python3 -m pytest -q` 为 **14 passed，2 个已有 collection warnings**；`validate_public_candidates.py`、`validate_pilot.py`、`paper/validate_draft.py` 均 PASS。后者只校验引用闭包、占位符和口径约束，草稿仍有 9 个明确结果占位符。以上 PASS 不验证方法有效性；反向样例正说明既有测试覆盖不足。

## 6. 下一步按什么顺序推进

1. **先修判定和 runner 门槛。** 将本轮四个 negative controls 加为应拒绝的回归测试；实现 import/调用绑定、可达性、有效断言与 test collection 检查；未知代码返回未决。新增 empty/skip/truncated-response 控制。验收：不能再静态真空通过，所有正向状态有明确证据。
2. **打通真实候选的可执行 probe 接口。** 先选一个确定性 API family，登记输入和观察适配，确保探针运行的是候选逻辑。版本对齐后保存源/目标双轨迹、独立 oracle 和最小反例。CuPy 环境未就绪时可先做已可执行方向，但不得将其标为 KATRER 结果。
3. **冻结独立的小型评估集。** 拆分原子条款；覆盖正确候选、目标绕过、目标已绑定但语义错误、环境不可用与未知映射；完成独立复核。先冻结规则，再开放 held-out family。
4. **做等预算对照，而非先扩生成量。** RQ1 加 target-binding baseline；RQ2 固定 checker/candidates，只换 original/random/boundary/clause-aware 策略，计有效探针与失败成本。LLM judgement 只作 baseline，不作 ground truth。
5. **根据结果决定贡献范围。** 若通用检验与条款探针有稳定收益，再做条件精化及真实 issue/PR 外部验证；若优势只在 import 检查或手工 mutant，应调整主张，不能靠扩大样本掩盖方法不足。若拿不到原 KATRER 中间产物，继续透明保留 inspired pilot，论文不将其包装成官方 baseline。

当前可对外表述：已建立可追溯的公开候选索引、13 条受控性质案例及 3 条 KATRER-inspired 模型生成样例；正在补齐自动检验、真实目标运行和独立评估，尚未得到 RQ1–RQ3 的有效性结果。
