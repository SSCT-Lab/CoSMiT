# 30 条扩充候选：动态执行与反例验证

本次实际执行了全部 30 条公开候选。结果为 **26 条在已测试输入上获得支持、3 条存在已重放的迁移问题、1 条目标绑定未决**。未修改原始候选代码，没有调用模型。

## 实际工作量

| 项目 | 数量 |
| --- | ---: |
| 候选 / 操作家族 | 30 / 15 |
| 生成的不同输入 | 1,920（每候选 64） |
| 通过源端执行与参考检查的输入 | 1,904 |
| 源端不合格输入 | 16，全部来自 E021 |
| 主实验源端执行 | 5,760 |
| 主实验目标端执行 / 已完成源目标对 | 5,712 |
| 观测透明性复验 | 180 次单侧执行 |
| 所有失败输入的无包装重放 | 288 次单侧执行 |
| 失败输入 / 问题候选 | 48 / 3 |

每个输入实际重复执行 3 次。48 个失败输入对应主实验 144 对失败执行，并不是 144 个独立缺陷。源端不合格的 16 个输入保留在日志，不执行目标、不补入替代输入。主实验、透明性检查和反例重放合计 11,940 次单侧执行；试跑不计入这一批次。

## 已确认的三个问题

| 候选 | 输入条件与结果 | 证据与结论 |
| --- | --- | --- |
| E020，tf.transpose → PyTorch | `perm=None` 时源端按默认规则反转维度；目标执行 `a.permute(*perm)`，对 None 解包导致 TypeError | 16 个输入均复现，属于未保持源默认参数语义 |
| E029，torch.clip → TensorFlow | min 或 max 单侧为 None，源端正确进行单侧裁剪；目标无条件对两个界限执行 tf.cast，触发 ValueError | 16 个输入均复现，属于未处理合法可选界限 |
| E030，tf.clip_by_value → PyTorch | 标量输入与标量界限时，源输出 shape=[]，目标输出 shape=[1]；例如 0.0 变为 [0.0] | 16 个输入均复现，属于输出形状变化，数值相同 |

E030 的原因是目标代码用 `clip_value_max.new_ones(1)` 构造长度 1 的向量，后续界限和 clamp 输出随之广播成向量。该结果违反源函数保持输入 shape 的性质。

本地实际运行版本的源 API docstring 已随运行记录保存：tf.transpose 说明省略 perm 时反转轴序；torch.clamp 说明单侧 None 表示无该侧界限，torch.clip 为其别名；tf.clip_by_value 说明输出保持输入类型和形状。源端实际输出同时通过预先生成的参考检查。

48 个输入全部再次执行未经调用包装的原函数，源／目标观察与主实验相同。E020 的 Python 异常文本会显示被调用函数的名称，包装执行显示 wrap，原执行显示 Tensor.permute；验证只规范化这段函数名，保留相同的 TypeError 和 None 解包诊断。没有把包装器引入的差异认作候选错误。

## E021 为什么保持未决

源代码显式调用 `torch.squeeze(input, dim)`。当 dim=None 时，当前 PyTorch 2.9.1 源函数触发 RuntimeError（把 None 作为维度名称处理），16 个输入因此不具备有效源端。没有把它们计作迁移反例。

另 16 个输入指定非单位轴，源行为是保持输入不变；目标代码走 `return input` 分支，输出正确但没有调用 tf.squeeze。当前实际目标调用门槛将其保留为 unbound。**这是有语义理由的恒等分支，不是已确认行为错误。** 剩余 32 个输入行为与目标绑定均通过。后续可以单独设计恒等分支证据规则，不能直接把未调用算子等同于迁移错误。

## 与既有比较器的关系

本次对双方成功产生数值输出的观察重算了 DLLens dense 比较分支：展平输出后 `allclose(atol=0.1, rtol=1e-5)`。E030 的全部 16 个失败输入均被该比较器接受；显式形状检查提供了 1 个候选上的额外区分证据。

E020/E029 是目标异常，不能送入纯数值比较，因此 DLLens 数值字段记为 null。本次没有重跑 DLLens 完整异常处理流程，不能宣称它漏检这两个案例。也没有运行 DocTer、IntentTester 或 LLM 组件；这不是全方法评估完成的报告。

## 验证方式与范围

参数适配支持 tensor、literal/None 和 tensor-list；观测记录包含 torch.Tensor.view/permute/squeeze/unsqueeze 等实例方法。源和目标运行在各自的框架进程中，每次调用重新构造输入，固定 CPU 单线程。

先冻结 1,920 个输入及参考，再执行所有源候选，保存源端资格结果，最后只对合格输入执行目标。参考使用 Python 标量算术及 NumPy 的形状／索引操作，未读取目标输出。float32 数值容差为 atol=1e-6、rtol=1e-5；float64 为 1e-12/1e-12；纯形状操作按精确值检查。没有事后调整容差。

前期输入设计的通用文字写了 rank≤3，但同时明确列出 squeeze 的 [1,2,1,3] 场景；本次执行协议在目标运行前明确该场景允许 rank=4，其余按已设计形状执行。输入去重发现 E030 两个结构层重复，因此在运行框架前将第四层落实为“界限等于输入端点”，符合原输入设计。所有最终输入均唯一且保留。

`verify_execution.py` 单独复算输入身份、源端资格门槛、重复稳定性、候选条款结果、数值比较、无包装重放及文件哈希，校验通过。原始 60 份函数的哈希与选择清单一致。

环境：Python 3.11.16、NumPy 2.4.6、PyTorch 2.9.1+cpu / TensorFlow 2.20.0。与师兄历史 NumPy 版本不同，作为独立新批次报告。结果针对公开 API counterpart 和有限输入，不是完整测试断言保持证明、盲测、独立人工 gold 或全域正确率。反例未最小化。

## 文件与复现

- 本目录 `summary.json`、`case-results.json`、`counterexamples.json`、`verification.json`：可阅读的结果、全部 48 个反例输入及验证摘要。
- `../runs/2026-09-20-dynamic-v3/`：权威完整运行，包含冻结输入、两侧观察、源端资格、API 文档、命令、异常与所有重放日志。
- `../runs/2026-09-20-dynamic-v1/`：输入重复预检停止，未执行框架。
- `../runs/2026-09-20-dynamic-v2/`：原始异常文本严格比较未通过的试跑；已保留，不混入最终计数。

从项目根目录校验：

```powershell
& F:/environment/python/miniconda3/envs/torch291/python.exe datasets/expansion-2026-09-18/tools/verify_execution.py datasets/expansion-2026-09-18/runs/2026-09-20-dynamic-v3
```

完整重放须指定不存在的新输出目录：

```powershell
& F:/environment/python/miniconda3/envs/torch291/python.exe datasets/expansion-2026-09-18/tools/execute_expansion.py --output datasets/expansion-2026-09-18/runs/NEW --pytorch-python F:/environment/python/miniconda3/envs/torch291/python.exe --tensorflow-python F:/environment/python/miniconda3/envs/tf220/python.exe
```

执行脚本需要本地 `local-sources` 中的原候选代码。原选择清单、协议草案和哈希未改写；其“未执行”状态描述的是 9 月 18 日选择时点，当前执行状态以本报告为准。
