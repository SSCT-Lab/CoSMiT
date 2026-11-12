# 意图不保持的原因、案例与核查依据

109组已标注候选：41组意图保持、68组意图不保持。下表覆盖全部68组负例，按已确认的主要义务分类；同一候选可属于多类，各行数量不能相加作为独立案例总数。

口径：这是现有人工意图标签的原因汇总，包含原公开测试义务比较及部分完整函数适配能力分析；不是当前基线输入包上的意图正确率，也不将行为差异当作意图缺失。既有意图标签未在此轮行为修订中改写。

|原因|数量|全部候选编号|核查依据|
|---|---:|---|---|
|数值范围或边界覆盖收窄|21|D0001、D0002、D0003、D0004、D0006、D0008、D0013、D0015、D0020、D0021、D0048、E002、E004、E006、E008、E017、E026、H004、H005、H006、H009|D0002等排除靠近±1的合法区域；D0015、H009遗漏极小非零数；E017、E026排除源允许的生成区间端点。|
|dtype类别覆盖遗漏|18|D0009、D0011、D0016、D0017、D0021、D0029、D0034、D0037、D0043、D0052、D0055、D0059、D0062、D0065、D0069、E026、H003、H004|显式将numeric、valid或float_and_complex等收窄为float，或明确过滤源类型；不把底层框架支持集合差异单独算作遗漏。|
|混合dtype组合遗漏|2|E025、E027|源允许不同浮点dtype组合；目标显式shared_dtype=True，只生成同类型数组。|
|形状、维数或数组数量覆盖收窄|9|D0021、E012、E022、E025、E026、H003、H004、H007、H009|E012/E022/H007遗漏零维输入；E025遗漏不同拼接轴长度；E026遗漏单数组及五维等场景；H003/H004/H009收窄矩阵或批量形状。|
|精度要求放宽|10|D0001、D0018、D0020、D0024、D0056、D0066、E002、E006、E008、H005|D0018的float32/64目标rtol=atol=1e-3，相对/绝对容差分别放宽100/1000倍；E008将atol从1e-6放宽到1。按dtype分别判断。|
|完整表达式或参数转换检查缺失|2|D0012、E019|D0012目标组件测试只检查exp，未覆盖exp(x)-1的减一；E019目标transpose测试未执行负轴归一化和交换轴排列构造。|
|默认参数或条件分支检查遗漏|4|E021、E022、E026、H007|E021目标公开测试未检查非单例轴恒等分支；E022遗漏axis=None；E026遗漏负轴；H007以单轴归约替代源默认全量归约。|
|设备参数化能力未保留|19|D0051、D0061、E001、E003、E005、E007、E009、E011、E013、E015、E020、E029、E030、H001、H002、H004、H008、H011、H012|源传递on_device，目标测试或受控适配未接收、转交该配置，或经CPU/NumPy中转；依据代码能力缺失，而非仅因本次在CPU运行。|
|梯度校验遗漏|2|D0053、D0063|源sign测试比较解析梯度与数值梯度；所选目标公开测试没有对应校验。|
|稀疏结构检查遗漏|2|D0053、D0063|源检查稀疏类型、indices、dense_shape及values；所选目标公开测试缺少对应结构断言。|

特别说明：E021当前行为已确认保持，但其原目标公开测试的分支义务标签仍不保持，两者评估对象不同。D0053/D0063在新受控适配中已有梯度/稀疏检查，不应把此表的原公开测试遗漏直接套到当前适配执行器。

## 逐候选追溯

|候选|原意图标签|原因分类|工作表|
|---|---|---|
|D0001|不保持（数值精度及输入范围）|数值范围或边界覆盖收窄；精度要求放宽|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0001/review.md)|
|D0002|不保持（输入覆盖收窄）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0002/review.md)|
|D0003|不保持（输入覆盖收窄）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0003/review.md)|
|D0004|不保持（输入覆盖收窄）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0004/review.md)|
|D0006|不保持（输入覆盖收窄）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0006/review.md)|
|D0008|不保持（输入覆盖收窄）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0008/review.md)|
|D0009|不保持（显式类型类别收窄）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0009/review.md)|
|D0011|不保持（显式类型类别收窄）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0011/review.md)|
|D0012|不保持（完整表达式检查缺失）|完整表达式或参数转换检查缺失|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0012/review.md)|
|D0013|不保持（输入覆盖收窄）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0013/review.md)|
|D0015|不保持（极小数覆盖改变）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0015/review.md)|
|D0016|不保持（显式类型类别收窄）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0016/review.md)|
|D0017|不保持（显式类型类别收窄）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0017/review.md)|
|D0018|不保持（精度要求放宽）|精度要求放宽|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0018/review.md)|
|D0020|不保持（精度及输入覆盖）|数值范围或边界覆盖收窄；精度要求放宽|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0020/review.md)|
|D0021|不保持（选定测试的输入及类型覆盖减少）|数值范围或边界覆盖收窄；dtype类别覆盖遗漏；形状、维数或数组数量覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0021/review.md)|
|D0024|不保持（bfloat16 精度要求放宽）|精度要求放宽|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0024/review.md)|
|D0029|不保持（显式过滤源类型）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0029/review.md)|
|D0034|不保持（显式删除复数类别）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0034/review.md)|
|D0037|不保持（显式过滤源类型）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0037/review.md)|
|D0043|不保持（显式删除复数类别）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0043/review.md)|
|D0048|不保持（大数输入覆盖收窄）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0048/review.md)|
|D0051|不保持（设备配置传递未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0051/review.md)|
|D0052|不保持（显式删除复数类别）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0052/review.md)|
|D0053|不保持（梯度及稀疏结构检查遗漏）|梯度校验遗漏；稀疏结构检查遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0053/review.md)|
|D0055|不保持（显式删除复数类别）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0055/review.md)|
|D0056|不保持（float32/64 精度要求放宽）|精度要求放宽|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0056/review.md)|
|D0059|不保持（显式缩小类型类别，遗漏复数）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0059/review.md)|
|D0061|不保持（设备参数化运行能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0061/review.md)|
|D0062|不保持（显式删除复数类别）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0062/review.md)|
|D0063|不保持（梯度及稀疏结构检查遗漏）|梯度校验遗漏；稀疏结构检查遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0063/review.md)|
|D0065|不保持（显式删除复数类别）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0065/review.md)|
|D0066|不保持（float32/64 精度要求放宽）|精度要求放宽|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0066/review.md)|
|D0069|不保持（显式缩小类型类别，遗漏复数）|dtype类别覆盖遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/D0069/review.md)|
|E001|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E001/review.md)|
|E002|不保持（精度及数值输入覆盖）|数值范围或边界覆盖收窄；精度要求放宽|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E002/review.md)|
|E003|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E003/review.md)|
|E004|不保持（数值输入范围收窄）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E004/review.md)|
|E005|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E005/review.md)|
|E006|不保持（精度及数值输入覆盖未保留）|数值范围或边界覆盖收窄；精度要求放宽|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E006/review.md)|
|E007|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E007/review.md)|
|E008|不保持（精度及输入覆盖未保留）|数值范围或边界覆盖收窄；精度要求放宽|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E008/review.md)|
|E009|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E009/review.md)|
|E011|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E011/review.md)|
|E012|不保持（零维输入覆盖遗漏）|形状、维数或数组数量覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E012/review.md)|
|E013|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E013/review.md)|
|E015|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E015/review.md)|
|E017|不保持（数值边界覆盖遗漏）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E017/review.md)|
|E019|不保持（轴参数转换的完整检查缺失）|完整表达式或参数转换检查缺失|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E019/review.md)|
|E020|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E020/review.md)|
|E021|不保持（非单例轴分支检查缺失）|默认参数或条件分支检查遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E021/review.md)|
|E022|不保持（默认轴及零维输入覆盖遗漏）|形状、维数或数组数量覆盖收窄；默认参数或条件分支检查遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E022/review.md)|
|E025|不保持（拼接轴长度差异及混合dtype覆盖遗漏）|混合dtype组合遗漏；形状、维数或数组数量覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E025/review.md)|
|E026|不保持（类型、形状、数组数量及轴覆盖收窄）|数值范围或边界覆盖收窄；dtype类别覆盖遗漏；形状、维数或数组数量覆盖收窄；默认参数或条件分支检查遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E026/review.md)|
|E027|不保持（混合浮点dtype覆盖遗漏）|混合dtype组合遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E027/review.md)|
|E029|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E029/review.md)|
|E030|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/E030/review.md)|
|H001|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H001/review.md)|
|H002|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H002/review.md)|
|H003|不保持（矩阵大小及类型类别收窄）|dtype类别覆盖遗漏；形状、维数或数组数量覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H003/review.md)|
|H004|不保持（形状、类型、数值范围及设备参数遗漏）|数值范围或边界覆盖收窄；dtype类别覆盖遗漏；形状、维数或数组数量覆盖收窄；设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H004/review.md)|
|H005|不保持（数值范围收窄及精度放宽）|数值范围或边界覆盖收窄；精度要求放宽|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H005/review.md)|
|H006|不保持（数值输入范围收窄）|数值范围或边界覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H006/review.md)|
|H007|不保持（全量归约及零维输入检查遗漏）|形状、维数或数组数量覆盖收窄；默认参数或条件分支检查遗漏|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H007/review.md)|
|H008|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H008/review.md)|
|H009|不保持（批量维度及极小数范围收窄）|数值范围或边界覆盖收窄；形状、维数或数组数量覆盖收窄|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H009/review.md)|
|H011|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H011/review.md)|
|H012|不保持（设备参数化能力未保留）|设备参数化能力未保留|[核查依据](C:/Users/33137/Desktop/completed-annotation-package-2026-11-6/annotation-package-2026-10-30/candidates/H012/review.md)|
