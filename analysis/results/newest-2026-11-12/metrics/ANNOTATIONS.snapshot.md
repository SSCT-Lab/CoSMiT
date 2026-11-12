# 109组统一标注表

2026-11-09：22组行为结论按用户确认的修订建议更新，当前材料入口见各工作表。其他87组及所有原意图标签保留；意图与本轮行为的评估范围不同，不能直接视为统一范围gold。

本轮主比较标注范围为109组（原主集79组、扩充集30组）；D0050不需要标注，详见[排除说明](EXCLUSIONS.md)。

每组只填这一行和链接的同一份工作表，不再分v3/v4或公开测试/适配表。所有材料已归入对应候选入口。

行为、意图可选：保持／不保持／证据不足／不适用。材料资格可选：可评／部分可评／需补材料／不适用。待标注不是结论。结论必须注明场景/范围及证据文件，不将不同实现或不同输入上的结论强行合并。

本轮 D0001–D0040 按[意图标注口径复查](reviewer-evidence/intent-scope-review-2026-11-05/REPORT.md)更新：测试代码明确表达的义务与底层环境覆盖分别记录；D0028 不在本包候选中。

E001–E030 已按[输入来源口径复查](reviewer-evidence/input-origin-review-2026-11-06/REPORT.md)更新：输入来源不单独作为意图，输入范围与参数能力分别判断。

|候选／工作表|源API|目标调用|现有材料|材料资格|行为是否保持|意图是否保持|范围／证据|标注者／日期|
|---|---|---|---|---|---|---|---|---|
|[D0001](candidates/D0001/review.md)|`torch.abs`|`tf.abs`|两端现成测试|部分可评|保持（登记样本）|不保持（数值精度及输入范围）|observations.json：64 输入×3 次；公开测试精度及 float32 生成范围未保留，其余义务见工作表|薛嘉伟／2026-11-05|
|[D0002](candidates/D0002/review.md)|`torch.acos`|`tf.acos`|两端现成测试|部分可评|保持|不保持（输入覆盖收窄）|observations.json：64 输入×3 次满足容差；目标生成范围约 [-0.9091,0.9091]，遗漏靠近 ±1 的合法输入；详见工作表|薛嘉伟／2026-11-05|
|[D0003](candidates/D0003/review.md)|`torch.arccos`|`tf.acos`|两端现成测试|部分可评|保持|不保持（输入覆盖收窄）|observations.json：64 输入×3 次满足容差；两端均缩放，目标范围约 [-0.9091,0.9091]，遗漏靠近 ±1 的合法输入；详见工作表|薛嘉伟／2026-11-05|
|[D0004](candidates/D0004/review.md)|`torch.arcsin`|`tf.asin`|两端现成测试|部分可评|保持|不保持（输入覆盖收窄）|64 输入×3 次满足容差；目标遗漏靠近 ±1 的合法输入；详见工作表|薛嘉伟／2026-11-05|
|[D0005](candidates/D0005/review.md)|`torch.arctan`|`tf.math.atan`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；核心数值、shape、dtype 检查及输入生成配置对应；详见工作表|薛嘉伟／2026-11-05|
|[D0006](candidates/D0006/review.md)|`torch.asin`|`tf.asin`|两端现成测试|部分可评|保持|不保持（输入覆盖收窄）|64 输入×3 次满足容差；目标遗漏靠近 ±1 的合法输入；详见工作表|薛嘉伟／2026-11-05|
|[D0007](candidates/D0007/review.md)|`torch.atan`|`tf.math.atan`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；核心数值、shape、dtype 检查及输入生成配置对应；详见工作表|薛嘉伟／2026-11-05|
|[D0008](candidates/D0008/review.md)|`torch.ceil`|`tf.math.ceil`|两端现成测试|部分可评|保持|不保持（输入覆盖收窄）|64 输入×3 次输出一致；目标边界约 [-18.18,18.18]，遗漏源测试的大数输入；详见工作表|薛嘉伟／2026-11-05|
|[D0009](candidates/D0009/review.md)|`torch.cos`|`tf.cos`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（显式类型类别收窄）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/D0009/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-05；2026-11-09 用户确认修订|
|[D0010](candidates/D0010/review.md)|`torch.cosh`|`tf.cosh`|两端现成测试|部分可评|保持|保持|64 输入×3 次输出一致；共同浮点检查与生成配置对应，目标类别增加复数|薛嘉伟／2026-11-05|
|[D0011](candidates/D0011/review.md)|`torch.exp`|`tf.exp`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（显式类型类别收窄）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/D0011/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-05；2026-11-09 用户确认修订|
|[D0012](candidates/D0012/review.md)|`torch.expm1`|`tf.exp`|两端现成测试|部分可评|保持|不保持（完整表达式检查缺失）|64 输入×3 次满足容差；源测试检查 expm1，即 exp(x)-1；目标公开测试仅检查 tensorflow.math.exp，没有执行完整目标表达式中的减一操作。即使包装函数遗漏减一，该组件测试也不能检出，未保留完整输出值检查。两端生成器均选择 float，使用相同默认参数和容差，但检查目标不同。|薛嘉伟／2026-11-05|
|[D0013](candidates/D0013/review.md)|`torch.floor`|`tf.floor`|两端现成测试|部分可评|保持|不保持（输入覆盖收窄）|64 输入×3 次满足容差；两端均选择 float，使用相同检查器和容差。两端均经过 1.1 线性缩放；源从 dtype 边界出发，目标从 [-20,20] 出发，边界约 [-18.18,18.18]，遗漏源允许的 100.5 等较大数值。该目标边界仍覆盖登记区间 [-8,8]。|薛嘉伟／2026-11-05|
|[D0014](candidates/D0014/review.md)|`torch.log`|`tf.math.log`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；共同浮点生成配置及检查对应|薛嘉伟／2026-11-05|
|[D0015](candidates/D0015/review.md)|`torch.log1p`|`tf.math.log1p`|两端现成测试|部分可评|保持|不保持（极小数覆盖改变）|64 输入×3 次满足容差；目标对数缩放提高极小非零输入下限；详见工作表|薛嘉伟／2026-11-05|
|[D0016](candidates/D0016/review.md)|`torch.neg`|`tf.negative`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（显式类型类别收窄）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/D0016/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-05；2026-11-09 用户确认修订|
|[D0017](candidates/D0017/review.md)|`torch.negative`|`tf.negative`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（显式类型类别收窄）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/D0017/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-05；2026-11-09 用户确认修订|
|[D0018](candidates/D0018/review.md)|`torch.reciprocal`|`tf.math.reciprocal`|两端现成测试|部分可评|保持|不保持（精度要求放宽）|64 输入×3 次满足容差；目标 rtol/atol 均放宽至 1e-3；详见工作表|薛嘉伟／2026-11-05|
|[D0019](candidates/D0019/review.md)|`torch.round`|`tf.round`|两端现成测试|部分可评|保持|保持（默认整数舍入场景）|64 输入×3 次满足容差；默认整数舍入检查对应；decimals=1～5 的额外覆盖单列；详见工作表|薛嘉伟／2026-11-05|
|[D0020](candidates/D0020/review.md)|`torch.sigmoid`|`tf.sigmoid`|两端现成测试|部分可评|保持|不保持（精度及输入覆盖）|64 输入×3 次满足容差；目标 rtol/atol=1e-2，输入边界约 [-18.18,18.18]；详见工作表|薛嘉伟／2026-11-05|
|[D0021](candidates/D0021/review.md)|`torch.sign`|`tf.sign`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（选定测试的输入及类型覆盖减少）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/D0021/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-05；2026-11-09 用户确认修订|
|[D0022](candidates/D0022/review.md)|`torch.sin`|`tf.sin`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；核心检查与生成配置对应，测试声明的类型类别保留|薛嘉伟／2026-11-05|
|[D0023](candidates/D0023/review.md)|`torch.sinh`|`tf.sinh`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；核心检查与生成配置对应，测试声明的类型类别保留|薛嘉伟／2026-11-05|
|[D0024](candidates/D0024/review.md)|`torch.sqrt`|`tf.sqrt`|两端现成测试|部分可评|保持|不保持（bfloat16 精度要求放宽）|64 输入×3 次输出一致；bfloat16 相对容差放宽，float32/64 精度加强；dtype 覆盖保留|薛嘉伟／2026-11-05|
|[D0025](candidates/D0025/review.md)|`torch.square`|`tf.square`|两端现成测试|部分可评|保持|保持|64 输入×3 次输出一致；生成配置、检查及容差一致，两后端 CPU dtype 集合一致|薛嘉伟／2026-11-05|
|[D0026](candidates/D0026/review.md)|`torch.tan`|`tf.tan`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；核心检查及类型类别保留|薛嘉伟／2026-11-05|
|[D0027](candidates/D0027/review.md)|`torch.tanh`|`tf.tanh`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；代码表达的检查、输入类别及容差保留；后端支持集合差异单列|薛嘉伟／2026-11-05|
|[D0029](candidates/D0029/review.md)|`tf.abs`|`torch.abs`|两端现成测试|部分可评|保持|不保持（显式过滤源类型）|64 输入×3 次满足容差；源选择 numeric，目标在同一类别上新增显式 filter，排除 float16、bfloat16、uint8、int8、uint16、int16。float16 是已查询确认的源可用类型，目标主动删除该场景；不以其他类型是否实际可用扩大结论。|薛嘉伟／2026-11-05|
|[D0030](candidates/D0030/review.md)|`tf.acos`|`torch.acos`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；代码表达的检查、输入类别及容差保留；后端支持集合差异单列|薛嘉伟／2026-11-05|
|[D0031](candidates/D0031/review.md)|`tf.asin`|`torch.asin`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；代码表达的检查、输入类别及容差保留；后端支持集合差异单列|薛嘉伟／2026-11-05|
|[D0032](candidates/D0032/review.md)|`tf.atan`|`torch.atan`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；代码表达的检查、输入类别及容差保留；后端支持集合差异单列|薛嘉伟／2026-11-05|
|[D0033](candidates/D0033/review.md)|`tf.cos`|`torch.cos`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；代码表达的检查、输入类别及容差保留；后端支持集合差异单列|薛嘉伟／2026-11-05|
|[D0034](candidates/D0034/review.md)|`tf.cosh`|`torch.cosh`|两端现成测试|部分可评|保持|不保持（显式删除复数类别）|64 输入×3 次满足容差；源明确选择 float_and_complex，目标改为 float，删除复数类别。|薛嘉伟／2026-11-05|
|[D0035](candidates/D0035/review.md)|`tf.exp`|`torch.exp`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；代码表达的检查、输入类别及容差保留；后端支持集合差异单列|薛嘉伟／2026-11-05|
|[D0036](candidates/D0036/review.md)|`tf.floor`|`torch.floor`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；代码表达的检查、输入类别及容差保留；后端支持集合差异单列|薛嘉伟／2026-11-05|
|[D0037](candidates/D0037/review.md)|`tf.math.abs`|`torch.abs`|两端现成测试|部分可评|保持|不保持（显式过滤源类型）|64 输入×3 次满足容差；源选择 numeric，目标新增显式 filter 排除 float16 等类型；float16 是已查询确认的源可用类型，属于目标测试主动删除的场景。|薛嘉伟／2026-11-05|
|[D0038](candidates/D0038/review.md)|`tf.math.acos`|`torch.acos`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；代码表达的检查、输入类别及容差保留；后端支持集合差异单列|薛嘉伟／2026-11-05|
|[D0039](candidates/D0039/review.md)|`tf.math.asin`|`torch.asin`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；代码表达的检查、输入类别及容差保留；后端支持集合差异单列|薛嘉伟／2026-11-05|
|[D0040](candidates/D0040/review.md)|`tf.math.atan`|`torch.atan`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；代码表达的检查、输入类别及容差保留；后端支持集合差异单列|薛嘉伟／2026-11-05|
|[D0041](candidates/D0041/review.md)|`tf.math.ceil`|`torch.ceil`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；检查和类型类别保留，目标数值范围扩大|薛嘉伟／2026-11-05|
|[D0042](candidates/D0042/review.md)|`tf.math.cos`|`torch.cos`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；检查保留，类型类别从 float 扩为 numeric|薛嘉伟／2026-11-05|
|[D0043](candidates/D0043/review.md)|`tf.math.cosh`|`torch.cosh`|两端现成测试|部分可评|保持|不保持（显式删除复数类别）|64 输入×3 次满足容差；目标将 float_and_complex 改为 float，删除复数类别|薛嘉伟／2026-11-05|
|[D0044](candidates/D0044/review.md)|`tf.math.exp`|`torch.exp`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；核心检查保留，类型类别从 float 扩为 valid|薛嘉伟／2026-11-05|
|[D0045](candidates/D0045/review.md)|`tf.math.expm1`|`torch.expm1`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；两端直接检查 expm1，生成配置、类型类别与容差一致|薛嘉伟／2026-11-05|
|[D0046](candidates/D0046/review.md)|`tf.math.floor`|`torch.floor`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；核心检查和类型类别保留，目标数值范围扩大|薛嘉伟／2026-11-05|
|[D0047](candidates/D0047/review.md)|`tf.math.log`|`torch.log`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；两端检查、生成配置、类型类别及容差一致|薛嘉伟／2026-11-05|
|[D0048](candidates/D0048/review.md)|`tf.math.log1p`|`torch.log1p`|两端现成测试|部分可评|保持|不保持（大数输入覆盖收窄）|64 输入×3 次满足容差；目标数值范围约 [-9090.91,9090.91]，遗漏源允许的大数输入；设备参数传递差异另列|薛嘉伟／2026-11-05|
|[D0049](candidates/D0049/review.md)|`tf.math.negative`|`torch.neg`|两端现成测试|部分可评|保持|保持|64 输入×3 次满足容差；核心检查保留，signed_integer/float 扩为 numeric；negative 与 neg 按材料别名对应|薛嘉伟／2026-11-05|
|[D0051](candidates/D0051/review.md)|`tf.math.round`|`torch.round`|两端现成测试|部分可评|保持|不保持（设备配置传递未保留）|192 条行为记录满足容差；设备配置传递未保留，逐项义务见工作表|薛嘉伟／2026-11-05|
|[D0052](candidates/D0052/review.md)|`tf.math.sigmoid`|`torch.sigmoid`|两端现成测试|部分可评|保持|不保持（显式删除复数类别）|192 条行为记录满足容差；显式删除复数类别，逐项义务见工作表|薛嘉伟／2026-11-05|
|[D0053](candidates/D0053/review.md)|`tf.math.sign`|`torch.sign`|两端现成测试|部分可评|保持|不保持（梯度及稀疏结构检查遗漏）|192 条行为记录满足容差；梯度及稀疏结构检查遗漏，逐项义务见工作表|薛嘉伟／2026-11-05|
|[D0054](candidates/D0054/review.md)|`tf.math.sin`|`torch.sin`|两端现成测试|部分可评|保持|保持|192 条行为记录满足容差；检查、类型类别、生成配置及设备传递保持|薛嘉伟／2026-11-05|
|[D0055](candidates/D0055/review.md)|`tf.math.sinh`|`torch.sinh`|两端现成测试|部分可评|保持|不保持（显式删除复数类别）|192 条行为记录满足容差；float_and_complex 改为 float，删除复数类别|薛嘉伟／2026-11-05|
|[D0056](candidates/D0056/review.md)|`tf.math.sqrt`|`torch.sqrt`|两端现成测试|部分可评|保持|不保持（float32/64 精度要求放宽）|192 条行为记录输出一致；目标 float32/64 容差放宽至 rtol=atol=1e-3，其他类型单列|薛嘉伟／2026-11-05|
|[D0057](candidates/D0057/review.md)|`tf.math.square`|`torch.square`|两端现成测试|部分可评|保持|保持|192 条行为记录输出一致；检查、生成配置、容差及设备传递一致|薛嘉伟／2026-11-05|
|[D0058](candidates/D0058/review.md)|`tf.math.tan`|`torch.tan`|两端现成测试|部分可评|保持|保持|192 条行为记录满足容差；检查、生成配置、容差及设备传递一致|薛嘉伟／2026-11-05|
|[D0059](candidates/D0059/review.md)|`tf.math.tanh`|`torch.tanh`|两端现成测试|部分可评|保持|不保持（显式缩小类型类别，遗漏复数）|192 条行为记录满足容差；源 valid 改为目标 float，复数检查遗漏|薛嘉伟／2026-11-05|
|[D0060](candidates/D0060/review.md)|`tf.negative`|`torch.negative`|两端现成测试|部分可评|保持|保持|192 条行为记录满足容差；核心检查保留，类型类别扩大|薛嘉伟／2026-11-05|
|[D0061](candidates/D0061/review.md)|`tf.round`|`torch.round`|两端现成测试|部分可评|保持|不保持（设备参数化运行能力未保留）|192 条行为记录输出一致；默认整数舍入检查保持，目标未传 on_device，使用默认 CPU；已由标注者核查确认|薛嘉伟／2026-11-05|
|[D0062](candidates/D0062/review.md)|`tf.sigmoid`|`torch.sigmoid`|两端现成测试|部分可评|保持|不保持（显式删除复数类别）|192 条行为记录满足容差；float_and_complex 改为 float，遗漏复数检查|薛嘉伟／2026-11-05|
|[D0063](candidates/D0063/review.md)|`tf.sign`|`torch.sign`|两端现成测试|部分可评|保持|不保持（梯度及稀疏结构检查遗漏）|192 条行为记录满足容差；普通前向检查保留，源梯度及稀疏结构断言未保留|薛嘉伟／2026-11-05|
|[D0064](candidates/D0064/review.md)|`tf.sin`|`torch.sin`|两端现成测试|部分可评|保持|保持|192 条行为记录满足容差；检查、生成配置、容差及设备传递一致|薛嘉伟／2026-11-05|
|[D0065](candidates/D0065/review.md)|`tf.sinh`|`torch.sinh`|两端现成测试|部分可评|保持|不保持（显式删除复数类别）|192 条行为记录满足容差；float_and_complex 改为 float，复数检查遗漏|薛嘉伟／2026-11-05|
|[D0066](candidates/D0066/review.md)|`tf.sqrt`|`torch.sqrt`|两端现成测试|部分可评|保持|不保持（float32/64 精度要求放宽）|192 条行为记录输出一致；目标 float32/64 容差放宽至 rtol=atol=1e-3，其他类型单列|薛嘉伟／2026-11-05|
|[D0067](candidates/D0067/review.md)|`tf.square`|`torch.square`|两端现成测试|部分可评|保持|保持|192 条行为记录输出一致；检查、生成配置、容差及设备传递一致|薛嘉伟／2026-11-05|
|[D0068](candidates/D0068/review.md)|`tf.tan`|`torch.tan`|两端现成测试|部分可评|保持|保持|192 条行为记录满足容差；检查、生成配置、容差及设备传递一致|薛嘉伟／2026-11-05|
|[D0069](candidates/D0069/review.md)|`tf.tanh`|`torch.tanh`|两端现成测试|部分可评|保持|不保持（显式缩小类型类别，遗漏复数）|192 条行为记录满足容差；源 valid 改为目标 float，复数检查遗漏|薛嘉伟／2026-11-05|
|[E001](candidates/E001/review.md)|`torch.add`|`tf.add, tf.cast`|两端测试＋完整函数适配（24条）|部分可评|不保持（混合类型适配样本）；原同类型域保持|不保持（设备参数化能力未保留）|行为结论及原/适配样本反例见工作表；核心输出检查保持；意图仅据 on_device 配置未传递判不保持，随机转固定不作理由。|薛嘉伟／2026-11-06|
|[E002](candidates/E002/review.md)|`tf.add`|`torch.add`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（精度及数值输入覆盖）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E002/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-05；2026-11-09 用户确认修订|
|[E003](candidates/E003/review.md)|`torch.sub`|`tf.cast, tf.subtract`|两端测试＋完整函数适配（24条）|部分可评|不保持（混合类型适配样本）；原同类型域保持|不保持（设备参数化能力未保留）|行为结论及原/适配样本反例见工作表；核心输出检查保持；意图仅据 on_device 配置未传递判不保持，随机转固定不作理由。|薛嘉伟／2026-11-06|
|[E004](candidates/E004/review.md)|`tf.subtract`|`torch.sub`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（数值输入范围收窄）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E004/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-05；2026-11-09 用户确认修订|
|[E005](candidates/E005/review.md)|`torch.mul`|`tf.cast, tf.multiply`|两端测试＋完整函数适配（19条）|部分可评|不保持（补充适配样本）；原同类型浮点登记域保持|不保持（设备参数化能力未保留）|行为结论及原/适配样本反例见工作表；核心输出检查保持；意图仅据 on_device 配置未传递判不保持，随机转固定不作理由。|薛嘉伟／2026-11-06|
|[E006](candidates/E006/review.md)|`tf.multiply`|`torch.mul`|两端现成测试|部分可评|保持|不保持（精度及数值输入覆盖未保留）|目标限制 [-10000,10000]，线性缩放后约 [-9090.91,9090.91]，比源默认浮点范围小；float32/64 的 rtol 从1e-5放宽到1e-3，atol仍为1e-6。|薛嘉伟／2026-11-05|
|[E007](candidates/E007/review.md)|`torch.div`|`tf.cast, tf.divide`|两端测试＋完整函数适配（25条）|部分可评|不保持（补充适配样本）；原同类型浮点登记域保持|不保持（设备参数化能力未保留）|行为结论及原/适配样本反例见工作表；核心输出检查保持；意图仅据 on_device 配置未传递判不保持，随机转固定不作理由。|薛嘉伟／2026-11-06|
|[E008](candidates/E008/review.md)|`tf.divide`|`torch.div`|两端现成测试|部分可评|保持|不保持（精度及输入覆盖未保留）|目标 atol 从默认1e-6放宽到1；log缩放2.5收窄数值范围，并新增 assume 排除 np.isclose(other,0) 的分母，遗漏源允许的1e-9等接近零输入。|薛嘉伟／2026-11-05|
|[E009](candidates/E009/review.md)|`torch.maximum`|`tf.cast, tf.maximum`|两端测试＋完整函数适配（24条）|部分可评|不保持（当前基线实例）|不保持（设备参数化能力未保留）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E009/README.md)：当前bool输入源端成功，目标端不支持并报错；以此替换旧混合dtype反例理由。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[E010](candidates/E010/review.md)|`tf.maximum`|`torch.maximum`|两端现成测试|部分可评|不保持（当前基线实例）|保持|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E010/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-05；2026-11-09 用户确认修订|
|[E011](candidates/E011/review.md)|`torch.minimum`|`tf.cast, tf.minimum`|两端测试＋完整函数适配（21条）|部分可评|不保持（当前基线实例）|不保持（设备参数化能力未保留）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E011/README.md)：当前bool输入源端成功，目标端不支持并报错；以此替换旧混合dtype反例理由。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[E012](candidates/E012/review.md)|`tf.minimum`|`torch.min`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（零维输入覆盖遗漏）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E012/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-05；2026-11-09 用户确认修订|
|[E013](candidates/E013/review.md)|`torch.pow`|`tf.cast, tf.pow`|两端测试＋完整函数适配（24条）|部分可评|不保持（当前基线实例）|不保持（设备参数化能力未保留）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E013/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[E014](candidates/E014/review.md)|`tf.math.pow`|`torch.pow`|两端现成测试|部分可评|保持|保持|原192条数值、shape、dtype一致；两端均检查两个同类型数组的幂运算，生成值域1–7，目标增加 on_device 传递；后端dtype支持差异单列。|薛嘉伟／2026-11-05|
|[E015](candidates/E015/review.md)|`torch.atan2`|`tf.atan2, tf.cast`|两端测试＋完整函数适配（23条）|部分可评|保持（当前基线实例及已检查性质）|不保持（设备参数化能力未保留）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E015/README.md)：旧失败场景不在当前已检查实例中；本批检查未发现违例。旧不保持结论及反例仅作为原范围历史证据，不推翻原结论。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[E016](candidates/E016/review.md)|`tf.atan2`|`torch.atan2`|两端现成测试|部分可评|保持|保持|原192条数值、shape、dtype一致；两端均检查 atan2 双输入并传递 on_device，目标取消同类型限制及第二参数近零过滤，输入覆盖扩大。|薛嘉伟／2026-11-05|
|[E017](candidates/E017/review.md)|`torch.reshape`|`tf.reshape`|两端现成测试|部分可评|保持|不保持（数值边界覆盖遗漏）|192条数值、shape、dtype一致；源通过 dtype_and_values 传入 exclude_min=False、exclude_max=False；目标直接使用 array_values 默认 True，排除源允许的生成区间端点。|薛嘉伟／2026-11-05|
|[E018](candidates/E018/review.md)|`tf.reshape`|`tensor.view`|两端现成测试|部分可评|保持|保持|192条数值、shape、dtype一致；两端核心输出、默认容差和 on_device 传递对应；目标纳入数值边界，未遗漏源输入覆盖。|薛嘉伟／2026-11-05|
|[E019](candidates/E019/review.md)|`torch.transpose`|`len, list, range, tf.transpose`|两端现成测试|部分可评|保持|不保持（轴参数转换的完整检查缺失）|原192条数值、shape、dtype一致；目标公开测试直接生成 perm，未检查包装函数的负轴处理及 dim0/dim1 到 perm 的转换。|薛嘉伟／2026-11-05|
|[E020](candidates/E020/review.md)|`tf.transpose`|`a.conj, a.permute`|两端测试＋完整函数适配（12条）|部分可评|保持（当前基线实例及已检查性质）|不保持（设备参数化能力未保留）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E020/README.md)：旧失败场景不在当前已检查实例中；本批检查未发现违例。旧不保持结论及反例仅作为原范围历史证据，不推翻原结论。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[E021](candidates/E021/review.md)|`torch.squeeze`|`tf.squeeze`|两端现成测试|部分可评|保持（当前48条基线输入及已检查性质）|不保持（非单例轴分支检查缺失）|[恒等分支复核](reviewer-evidence/E021-identity-review-2026-11-09/REPORT.md)：48输入×3次双端检查通过，23条直接返回、25条squeeze；原系统未决保留。意图仍为原公开测试口径。|薛嘉伟；2026-11-09 用户确认修订|
|[E022](candidates/E022/review.md)|`tf.squeeze`|`input.squeeze`|两端现成测试|部分可评|保持|不保持（默认轴及零维输入覆盖遗漏）|192条记录两端成功，数值、shape、dtype一致。源 _squeeze_helper 可生成 axis=None，表达一次删除全部单例维度的检查；目标方法测试 force_int_axis=True，仅检查指定整数轴，遗漏默认分支。源默认形状允许零维，目标 min_num_dims=1，另遗漏零维输入。|薛嘉伟／2026-11-05|
|[E023](candidates/E023/review.md)|`torch.unsqueeze`|`tf.expand_dims`|两端现成测试|部分可评|保持|保持|192条记录两端成功，数值、shape、dtype一致。两端使用同样的 dtype_and_values(valid)、共享 get_shape 以及允许负轴的 get_axis(force_int=True)，检查插入单例维度后的数值、shape、dtype。参数 dim 与 axis 对应。|薛嘉伟／2026-11-05|
|[E024](candidates/E024/review.md)|`tf.expand_dims`|`input.unsqueeze`|两端现成测试|部分可评|保持|保持|192条记录两端成功，数值、shape、dtype一致。两端输入类型、形状、数值和轴生成配置一致，轴允许负值。目标使用 torch.tensor 构造实例并执行 unsqueeze，公共方法检查器保留数值、shape、dtype检查，函数改为实例方法未遗漏核心义务。|薛嘉伟／2026-11-05|
|[E025](candidates/E025/review.md)|`torch.concat`|`tf.concat`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（拼接轴长度差异及混合dtype覆盖遗漏）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E025/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-05；2026-11-09 用户确认修订|
|[E026](candidates/E026/review.md)|`tf.concat`|`torch.cat`|两端现成测试|部分可评|保持|不保持（类型、形状、数组数量及轴覆盖收窄）|192条数值、shape、dtype一致；目标 numeric 改为 float，仅2–4个数组、1–4维、每维2–3，排除负轴与数值生成端点。|薛嘉伟／2026-11-05|
|[E027](candidates/E027/review.md)|`torch.stack`|`tf.stack`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（混合浮点dtype覆盖遗漏）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/E027/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[E028](candidates/E028/review.md)|`tf.stack`|`torch.stack`|两端现成测试|部分可评|保持|保持|192条数值、shape、dtype一致；源 shared_dtype=True；目标默认 shared_dtype=False，保留同类型场景并增加混合浮点类型组合。其他核心生成和检查配置对应。|薛嘉伟／2026-11-06|
|[E029](candidates/E029/review.md)|`torch.clip`|`tf.cast, tf.where`|两端测试＋完整函数适配（33条）|部分可评|不保持（单边裁剪）|不保持（设备参数化能力未保留）|行为结论及原/适配样本反例见工作表；核心输出检查保持；意图仅据 on_device 配置未传递判不保持，随机转固定不作理由。|薛嘉伟／2026-11-06|
|[E030](candidates/E030/review.md)|`tf.clip_by_value`|`clip_value_max.new_ones, float, torch.clamp, torch.max`|两端测试＋完整函数适配（17条）|部分可评|不保持（零维输出形状改变）|不保持（设备参数化能力未保留）|行为结论及原/适配样本反例见工作表；核心输出检查保持；意图仅据 on_device 配置未传递判不保持，随机转固定不作理由。|薛嘉伟／2026-11-06|
|[H001](candidates/H001/review.md)|`torch.prod`|`tf.reduce_prod`|两端测试＋完整函数适配（20条）|部分可评|不保持（整数适配样本）；原浮点登记域保持|不保持（设备参数化能力未保留）|原192条一致；适配20条中18通过、2失败，sample_index=1、18的int32输入在源输出int64、目标输出int32。核心输出检查保持；意图仅据设备配置未传递。|薛嘉伟／2026-11-06|
|[H002](candidates/H002/review.md)|`torch.matmul`|`tf.matmul`|两端测试＋完整函数适配（10条）|部分可评|保持（当前基线实例及已检查性质）|不保持（设备参数化能力未保留）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/H002/README.md)：旧失败场景不在当前已检查实例中；本批检查未发现违例。旧不保持结论及反例仅作为原范围历史证据，不推翻原结论。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[H003](candidates/H003/review.md)|`torch.det`|`tf.linalg.det`|两端现成测试|部分可评|保持|不保持（矩阵大小及类型类别收窄）|192条均满足登记容差，shape、dtype一致；目标方阵边长1–4遗漏源5×5场景，valid类型改为float。|薛嘉伟／2026-11-06|
|[H004](candidates/H004/review.md)|`torch.trace`|`tf.linalg.trace`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（形状、类型、数值范围及设备参数遗漏）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/H004/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[H005](candidates/H005/review.md)|`torch.cumsum`|`tf.cumsum`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（数值范围收窄及精度放宽）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/H005/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[H006](candidates/H006/review.md)|`torch.cumprod`|`tf.math.cumprod`|两端现成测试|部分可评|不保持（当前基线实例）|不保持（数值输入范围收窄）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/H006/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[H007](candidates/H007/review.md)|`tf.reduce_prod`|`torch.prod`|两端现成测试|部分可评|不保持（默认轴）；原显式轴登记域保持|不保持（全量归约及零维输入检查遗漏）|原显式轴192条一致；补跑axis=None时源返回24.0、目标RuntimeError。目标测试仅整数轴且至少一维。|薛嘉伟／2026-11-06|
|[H008](candidates/H008/review.md)|`tf.matmul`|`torch.matmul`|两端测试＋完整函数适配（12条）|部分可评|保持（已测试范围）|不保持（设备参数化能力未保留）|原192条一致；完整适配12条全部通过，包含转置处理。意图依据见工作表。|薛嘉伟／2026-11-06|
|[H009](candidates/H009/review.md)|`tf.linalg.det`|`torch.linalg.det`|两端现成测试|部分可评|保持|不保持（批量维度及极小数范围收窄）|192条均满足登记容差，shape、dtype一致。意图依据见工作表。|薛嘉伟／2026-11-06|
|[H010](candidates/H010/review.md)|`tf.linalg.trace`|`torch.diagonal`|两端测试＋完整函数适配（13条）|部分可评|不保持（补充适配样本）；原二维登记域保持|保持|原192条一致；完整适配13条中10通过、3失败：sample_index=1输出int32变int64，7的shape由(2,2,1)变(2,2)，11由(2,)变(2,1)。意图依据见工作表。|薛嘉伟／2026-11-06|
|[H011](candidates/H011/review.md)|`tf.cumsum`|`torch.cumsum`|两端测试＋完整函数适配（17条）|部分可评|不保持（当前基线实例）|不保持（设备参数化能力未保留）|[2026-11-09补充证据](reviewer-evidence/baseline-supplement-2026-11-09/cases/H011/README.md)：当前实例存在双端执行或输出差异；具体参数、输出与逐输入检查设置见补充材料。 意图仍为原公开测试口径。|薛嘉伟／2026-11-06；2026-11-09 用户确认修订|
|[H012](candidates/H012/review.md)|`tf.math.cumprod`|`torch.cumprod`|两端测试＋完整函数适配（14条）|部分可评|不保持；原默认浮点登记域保持|不保持（设备参数化能力未保留）|原192条一致；适配14条中2通过、12条因int32输出变int64失败；另补跑axis=1、exclusive=True时目标拼接报错。核心输出检查保留；意图仅据设备配置未传递。|薛嘉伟／2026-11-06|
