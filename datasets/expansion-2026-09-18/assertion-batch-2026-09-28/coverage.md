# 全部 30 个候选的证据状态

此表由 verification.json 汇总。所有人工复核和独立 gold 均待完成。基线通过只适用于选定方法、输入与 CPU 配置，不等于完整测试意图保持。

| 候选 | 算子 / 源框架 | 保留方法基线 | 形状扰动 | 数值扰动 | 限制或备注 |
|---|---|---|---|---|---|
| E001 | add / pytorch | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E002 | add / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E003 | subtract / pytorch | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E004 | subtract / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E005 | multiply / pytorch | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E006 | multiply / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E007 | divide / pytorch | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E008 | divide / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E009 | maximum / pytorch | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E010 | maximum / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E011 | minimum / pytorch | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E012 | minimum / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E013 | power / pytorch | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E014 | power / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E015 | atan2 / pytorch | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E016 | atan2 / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 保留 helper 全文；输入为扩充集索引 0、16 |
| E017 | reshape / pytorch | 未执行：源义务未解决 | 未决 | 未决 | 共享存储/别名及修改传播义务未覆盖 |
| E018 | reshape / tensorflow | 双方通过 | 双方断言拒绝 | 源测试不拒绝（非丢失） | 原测试仅检查形状，不能要求其拒绝数值扰动 |
| E019 | transpose / pytorch | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 限定原方法与选定 CPU 配置 |
| E020 | transpose / tensorflow | 目标未通过 | 基线不合格，不判敏感性 | 基线不合格，不判敏感性 | 目标 permute(*None) TypeError；已知行为问题 |
| E021 | squeeze / pytorch | 未执行：源义务未解决 | 未决 | 未决 | 共享存储/别名义务未覆盖；原始行为层另有源输入无效与绑定未决 |
| E022 | squeeze / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 限定原方法与选定 CPU 配置 |
| E023 | expand_dims / pytorch | 未执行：源义务未解决 | 未决 | 未决 | 共享存储/别名及修改传播义务未覆盖 |
| E024 | expand_dims / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 限定原方法与选定 CPU 配置 |
| E025 | concat / pytorch | 双方通过 | 扰动触发运行异常，未决 | 双方断言拒绝 | 形状扰动使 narrow 在断言前发生 RuntimeError |
| E026 | concat / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 原方法比较 list/tuple 两种调用，并非独立完整参考值 |
| E027 | stack / pytorch | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 限定原方法与选定 CPU 配置 |
| E028 | stack / tensorflow | 目标未通过 | 基线不合格，不判敏感性 | 基线不合格，不判敏感性 | float8 参数转换失败属于适配限制，不能计为候选缺陷 |
| E029 | clip / pytorch | 目标未通过 | 基线不合格，不判敏感性 | 基线不合格，不判敏感性 | 目标转换 None 为 Tensor 失败；已知行为问题 |
| E030 | clip / tensorflow | 双方通过 | 双方断言拒绝 | 双方断言拒绝 | 所选原测试为 2×3 输入；通过不能否定既有标量形状反例 |
