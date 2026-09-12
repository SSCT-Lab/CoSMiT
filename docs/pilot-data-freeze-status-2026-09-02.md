# CoSMiT Pilot 数据冻结进展

日期：2026-09-03  
阶段：M2 — 数据与标注标准冻结（进行中）

## 本轮完成

1. 将一个月实现目标从旧的 adapter synthesis/solver 路线统一为 candidate migration certification：Property IR、Candidate Mapping IR、obligation checker、clause-aware probe、counterexample minimization 和 condition refinement。
2. 冻结 15 个 API groups：12 个 development groups、3 个 evaluation-holdout groups。
3. 建立 45 个 property slots：开发集 36 条明确原子候选，留出集 9 个 sealed slots。留出集只公开 API family 与证据入口，IR v0.1 冻结前不得展开具体条款。
4. 完成 annotation guide v0.2：
   - 关系与证据状态正交；
   - `library-unsupported` 与 `dsl-out-of-grammar` 分离；
   - researcher mutants、evidence-derived references、公开系统输出和 repository migrations 分层；
   - 全量主标注 + 20%–30% 分层独立复核；
   - 真实输出、疑似目标问题和全部分歧强制复核。
5. 冻结基础独立复核样本 12/45（26.7%），每个 development group 覆盖一条，并建立 blind assignment、review form 和 adjudication form。
6. 将 10 条 feasibility records 按 v0.2 单一 oracle 重新原子化，并新增 variance 与 softmax 的 3 条 properties；当前共有 13 条 v0.2 provisional properties。
7. 将旧 10 条 seed 的 reference/mutant trace 转换为统一 v0.2 candidate-case schema。当前 13 条性质均包含一条 evidence-derived reference 和一条 researcher-constructed mutant，共 26 个候选认证 cases。
8. 建立固定环境动态 witness：
   - `CCP-031`：PyTorch 默认样本方差为 `0.5`，直接 TensorFlow population variance 为 `0.25`；乘以 `N/(N-1)` 后为 `0.5`；
   - `CCP-034`：遗漏 softmax 源轴时目标默认沿末轴归一化，候选可执行但值不保持；显式 `axis=0` 后保持；
   - `CCP-035`：遗漏显式 computation dtype 时目标返回 float16；先转换为 float32 后保持源输出 dtype。
9. 5 个新增官方证据 URL 均锚定固定 commit 并通过 HTTP 200 检查。

## 当前证据规模

- Feasibility 层：10 条旧 provisional properties、10 个 adapted witnesses、10 个 researcher-constructed naive candidates。
- Pilot v0.2 层：36 条明确开发候选 + 9 个 holdout slots；其中 13 条已经完成 v0.2 provisional primary annotation。
- 13 条性质形成 13 个 evidence-derived reference cases 和 13 个 researcher-constructed mutant cases，均已进入统一 v0.2 candidate-case schema。

## 验证结果

- `python3 benchmark/pilot/validate_pilot.py`：PASS；
- sampling 数量、ID 唯一性、8 个语义维度、holdout sealing、复核比例、blind-field contract、property/case/evidence/trace 引用均受机器检查；
- `pytest`：9 passed，保留 2 个既有 collection warnings；
- sampling manifest freeze hash：`f7054df2d32bd19549b8312ed9d51371194bd19491eca1c370b0eb681868cb66`。

## 尚未完成

M2 不能标记完成，剩余工作为：

1. 为剩余 23 条 development properties 逐条固定官方证据、valid/excluded domain 和 canonical candidate；
2. 完成全部 36 条 development primary annotations；
3. 在 IR v0.1 冻结后，由独立复核者展开 9 个 holdout slots；
4. 获得或构造与 provenance 分开的真实系统输出/历史迁移候选，否则最终只能报告 mutation detection，不能声称真实增量价值。

## 下一执行批次

下一批补齐 variance/softmax 剩余条款和其他 queued properties，目标是完成剩余 23 条 development primary annotations。完整 IR grammar 只有在 development primary ledger 稳定后冻结；holdout 在此之前保持 sealed。
