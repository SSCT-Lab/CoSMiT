# 扩充集的断言保持证据（2026-09-28）

## 结论与使用范围

全部 30 个候选已完成证据登记；可执行实验与离线核验已完成。27 个候选执行了保留上游测试方法或 helper 正文的实验，3 个因共享存储、别名和修改传播义务无法由当前跨框架数值桥接验证而保留未决。**这不是 30 个真实历史迁移测试的准确率实验，也没有证明完整测试意图保持。**

本批仅使用 `expansion-2026-09-18` 内的候选、counterpart 和冻结输入，并新增正式框架版本的上游测试快照。没有使用废弃 datasets 数据或 D0028。原始扩充数据及 9 月 20 日执行档案未修改。

逐项结果见 [coverage.md](coverage.md)，机器可读审计结果见 [verification.json](verification.json)，人工复核清单见 [review-status.json](review-status.json)。人工评审与独立 gold 均尚未完成。

## 两层实验分别回答什么

### 1. 全量协议诊断

`batch.py` 在 30 个候选的全部 1,920 个冻结输入上执行源/目标操作，并接入新写的断言续体。除 E018 只检查形状，其余检查值与形状。源目标断言按构造保持一致，不能用于估计真实迁移中断言丢失的发生率。

共 56,016 次单侧执行；1,904 个输入满足源端资格，1,856 个同时满足双方基线及敏感性检查门槛。16 个 E021 输入源端无效；E020、E029、E030 各有 16 个目标基线失败输入。没有发现新的意图丢失见证；这与断言按构造保留相一致。

执行模式包括 original、observe、reinject、wrong-shape、wrong-value，每种重复三次。observe 仅记录所选操作边界，不是通用 API 插桩。数值与形状扰动的精确定义在冻结 `manifest.json` 中。资格判断、原值重注入透明性和送达观察的一致性先于拒绝能力判断。

### 2. 保留上游方法正文的实验

`retained.py` 使用 TensorFlow v2.20.0 / PyTorch v2.9.1 的真实测试方法或 helper 正文，保留其中断言；明确选择 CPU/eager 配置后移除装饰器，仅替换登记的操作调用。源目标使用相同源框架断言 harness，跨框架结果通过值桥接返回。候选是本次新构造的操作替换版本，并非外部迁移工具的历史输出。

E001–E016 保留 helper 正文，但输入生成器替换为扩充集索引 0、16，不能宣称保留完整上游测试设置。其余 11 个执行登记的完整方法及所需 helper；运行配置与替换位置见 `retained/registration.json`。每个方法只扰动第一次返回观察，后续操作正常执行。

共 1,290 次单侧执行，覆盖 27 个候选、43 个场景：

| 结果 | 候选数 | 解释 |
|---|---:|---|
| 双方正常基线及原值重注入通过 | 24 | 仅支持已检查方法、输入和配置 |
| 目标 counterpart 执行失败 | 2 | E020 的默认 perm=None；E029 的单边 None 裁剪边界 |
| 目标参数适配失败 | 1 | E028 的 float8 转换限制；不能算候选缺陷 |
| 源义务未解决，未执行本层 | 3 | E017、E021、E023 的存储别名与修改传播 |

86 个“场景 × 扰动类型”结果为：78 个双方断言拒绝，1 个源测试不拒绝，6 个基线不合格，1 个扰动运行异常。**86 不是独立候选数，不能作为样本量计算准确率。**

- E018 的源方法仅检查形状，数值扰动被双方接受不构成意图丢失。
- E025 的形状扰动在 `narrow` 处触发 RuntimeError，未到达相关断言，不能算断言拒绝。
- E020、E028、E029 的正常基线未通过，早期扰动即使触发断言也不能用于敏感性结论。
- E030 的保留方法使用 2×3 输入；其通过不能推翻扩充集已有的标量形状差异。
- E026 的上游方法比较 list/tuple 调用结果，并不是独立完整参考值检查。

## 可复核档案

- `manifest.json`、`intake.json`、`registered-tests/`：运行前冻结的协议与候选。
- `run-01/`：全量协议诊断原始记录、过程输出和哈希。
- `retained/`：保留正文、操作替换登记及哈希。
- `retained-executions-v1.json`、`retained-runner-v1.py`：首轮记录；E028 缺少上游辅助函数，保留失败历史。
- `retained-executions-v2.json`、`retained.py`：补入原始 `np_split_squeeze` helper 后的有效全量运行；没有修补目标 counterpart。
- `source-provenance.json`：全部上游快照 URL 与 SHA-256；原文件保留版权信息。
- `verify_batch.py`：独立离线核验记录身份、完整性、重复稳定性、AST 正文与允许的替换、扰动计算、资格门槛及失败归类。
- `package-SHA256.json`：整理完成后的文件清单；不代替运行前冻结清单，也不证明独立人工标注。

运行环境为 Python 3.11.16、TensorFlow 2.20.0、PyTorch 2.9.1+cpu、NumPy 2.1.3。`expecttest` 仅装在本目录 `dependencies/`，供 PyTorch 上游测试 harness 使用。原始日志较大，保留用于追溯。

在仓库根目录离线复核（只需可导入 NumPy 的 Python；不重跑框架）：

```powershell
python datasets/expansion-2026-09-18/assertion-batch-2026-09-28/verify_batch.py
```

需要重跑时，使用上述框架环境，并指定新的输出路径，保留现有记录：

```powershell
python datasets/expansion-2026-09-18/assertion-batch-2026-09-28/batch.py run --python F:/environment/python/miniconda3/envs/tf220/python.exe --output datasets/expansion-2026-09-18/assertion-batch-2026-09-28/run-new
python datasets/expansion-2026-09-18/assertion-batch-2026-09-28/retained.py execute --output datasets/expansion-2026-09-18/assertion-batch-2026-09-28/retained-executions-new.json
```

## 论文可以据此补什么

可以补充可追溯的源断言登记、操作替换规则、受控扰动与资格门槛，以及带有明确限制的可行性实验。可以说明 E020/E029 的行为问题也能在保留真实上游测试正文时暴露。

仍需真实已有迁移测试及其来源、独立人工义务复核与 gold、未覆盖的别名语义，以及有独立依据的意图丢失反例，才能进一步评估验证器的准确率或真实迁移质量。目前没有把这些结果写成论文的完整意图保持或准确率结论。
