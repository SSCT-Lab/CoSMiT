# Independent Review Pack

本目录用于 CoSMiT candidate-certification pilot 的独立复核。基础复核样本由 sampling manifest 固定为 12/45（26.7%）；真实系统输出、repository migration、高风险诊断和所有分歧另行强制加入。

## Reviewer 可见信息

- 固定 commit 的源测试、目标测试、官方源码和文档；
- 待认证候选代码及其来源；
- 冻结环境与执行说明；
- 空白 `review-form.yaml`。

## Reviewer 不可见信息

- CoSMiT 的 supported/refuted/undetermined 输出；
- CoSMiT 生成的 probe、反例和条件；
- primary annotator 的关系、状态、诊断和 condition；
- baseline 或作者对候选正确性的结论。

## 工作步骤

1. 阅读 `assignment.yaml` 中的 case 列表；
2. 仅依据随 case 提供的官方证据和候选代码，独立填写一份 review form；
3. 先原子化源性质，再判断目标关系和候选状态；
4. 如果证据不足，使用 `undetermined`，不要猜测；
5. 不运行 CoSMiT；如需独立探针，在 form 中完整记录命令、输入、版本和输出；
6. 提交后再由协调者比较 primary/reviewer 结果并生成 adjudication，不允许在提交前互看标签。

当前包只完成 sampling 与表单冻结。case 证据包将在 primary property/evidence ledger 完成后由 `build_review_pack.py` 生成。
