# 110组本地基线重算（2026-10-19）

复用10月18日同一批观察；重新调用判定代码。未重跑原测试真实性核验，无模型请求。

|方法|候选级结果|
|---|---|
|cosmit|supported-on-tested-inputs: 80；refuted-on-tested-inputs: 28；undetermined: 2|
|dllens|no-difference-on-tested-inputs: 85；undetermined: 15；difference-observed: 10|
|dllens_source_tolerance|no-difference-on-tested-inputs: 85；undetermined: 15；difference-observed: 10|
|docter|satisfied: 43；undetermined: 53；violated: 14|

## 比较范围与适配说明

- CoSMiT为登记输出性质及调用行门槛；未声称完整测试意图判断。
- DLLens运行固定上游compare_res；保留squeeze/flatten及atol=0.1、默认rtol、equal_nan=True。bfloat16用精确float32表示，稀疏输出转dense供数值比较；不比较稀疏结构。
- dllens_source_tolerance仅替换为源测试数值容差，仍使用DLLens展平和equal_nan语义；这是敏感性对照，不是上游默认配置，也不是完整Ivy oracle。
- 框架异常/缺输出/比较器不支持均未决，不能作为DLLens漏检；同一候选其他可比较输入若发现差异则报告差异，并保留所有未决输入。
- DocTer沿用冻结API映射，对原参数重新计算；可选None按未提供处理，明确记录；rank使用显式shape避免空数组维数丢失。稀疏输入暂未决。
- DocTer历史版本兼容性未建立；约束违反不是意图不保持标签。缺映射和符号约束保留未决。
- 每个候选可有多条输入；重复、别名和失败记录不增加候选数；无独立gold，不计算Accuracy/P/R/F1。

## 逐候选结果

|候选|源API|CoSMiT|DLLens|DocTer|
|---|---|---|---|---|
|D0001|torch.abs|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0002|torch.acos|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0003|torch.arccos|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0004|torch.arcsin|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0005|torch.arctan|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0006|torch.asin|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0007|torch.atan|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0008|torch.ceil|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0009|torch.cos|refuted-on-tested-inputs|undetermined|satisfied|
|D0010|torch.cosh|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0011|torch.exp|refuted-on-tested-inputs|undetermined|satisfied|
|D0012|torch.expm1|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0013|torch.floor|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0014|torch.log|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0015|torch.log1p|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0016|torch.neg|refuted-on-tested-inputs|undetermined|satisfied|
|D0017|torch.negative|refuted-on-tested-inputs|undetermined|undetermined|
|D0018|torch.reciprocal|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0019|torch.round|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0020|torch.sigmoid|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0021|torch.sign|refuted-on-tested-inputs|difference-observed|satisfied|
|D0022|torch.sin|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0023|torch.sinh|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0024|torch.sqrt|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0025|torch.square|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0026|torch.tan|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0027|torch.tanh|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0029|tf.abs|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0030|tf.acos|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0031|tf.asin|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0032|tf.atan|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0033|tf.cos|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0034|tf.cosh|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0035|tf.exp|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0036|tf.floor|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0037|tf.math.abs|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0038|tf.math.acos|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0039|tf.math.asin|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0040|tf.math.atan|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0041|tf.math.ceil|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0042|tf.math.cos|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0043|tf.math.cosh|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0044|tf.math.exp|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0045|tf.math.expm1|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0046|tf.math.floor|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0047|tf.math.log|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0048|tf.math.log1p|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0049|tf.math.negative|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0050|tf.math.reciprocal|undetermined|no-difference-on-tested-inputs|undetermined|
|D0051|tf.math.round|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0052|tf.math.sigmoid|supported-on-tested-inputs|no-difference-on-tested-inputs|violated|
|D0053|tf.math.sign|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0054|tf.math.sin|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0055|tf.math.sinh|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0056|tf.math.sqrt|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0057|tf.math.square|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0058|tf.math.tan|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0059|tf.math.tanh|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0060|tf.negative|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0061|tf.round|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|D0062|tf.sigmoid|supported-on-tested-inputs|no-difference-on-tested-inputs|violated|
|D0063|tf.sign|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0064|tf.sin|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0065|tf.sinh|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0066|tf.sqrt|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0067|tf.square|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0068|tf.tan|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|D0069|tf.tanh|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|E001|torch.add|refuted-on-tested-inputs|difference-observed|satisfied|
|E002|tf.add|refuted-on-tested-inputs|undetermined|undetermined|
|E003|torch.sub|refuted-on-tested-inputs|difference-observed|undetermined|
|E004|tf.subtract|refuted-on-tested-inputs|undetermined|undetermined|
|E005|torch.mul|refuted-on-tested-inputs|difference-observed|satisfied|
|E006|tf.multiply|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|E007|torch.div|refuted-on-tested-inputs|difference-observed|violated|
|E008|tf.divide|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|E009|torch.maximum|refuted-on-tested-inputs|undetermined|undetermined|
|E010|tf.maximum|refuted-on-tested-inputs|difference-observed|undetermined|
|E011|torch.minimum|refuted-on-tested-inputs|undetermined|undetermined|
|E012|tf.minimum|refuted-on-tested-inputs|undetermined|undetermined|
|E013|torch.pow|refuted-on-tested-inputs|undetermined|violated|
|E014|tf.math.pow|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|E015|torch.atan2|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|E016|tf.atan2|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|E017|torch.reshape|supported-on-tested-inputs|no-difference-on-tested-inputs|violated|
|E018|tf.reshape|supported-on-tested-inputs|no-difference-on-tested-inputs|violated|
|E019|torch.transpose|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|E020|tf.transpose|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|E021|torch.squeeze|undetermined|no-difference-on-tested-inputs|satisfied|
|E022|tf.squeeze|supported-on-tested-inputs|no-difference-on-tested-inputs|violated|
|E023|torch.unsqueeze|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|E024|tf.expand_dims|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|E025|torch.concat|refuted-on-tested-inputs|undetermined|violated|
|E026|tf.concat|supported-on-tested-inputs|no-difference-on-tested-inputs|violated|
|E027|torch.stack|refuted-on-tested-inputs|undetermined|violated|
|E028|tf.stack|supported-on-tested-inputs|no-difference-on-tested-inputs|violated|
|E029|torch.clip|refuted-on-tested-inputs|undetermined|satisfied|
|E030|tf.clip_by_value|refuted-on-tested-inputs|no-difference-on-tested-inputs|violated|
|H001|torch.prod|refuted-on-tested-inputs|difference-observed|satisfied|
|H002|torch.matmul|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|H003|torch.det|supported-on-tested-inputs|no-difference-on-tested-inputs|violated|
|H004|torch.trace|refuted-on-tested-inputs|difference-observed|undetermined|
|H005|torch.cumsum|refuted-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|H006|torch.cumprod|refuted-on-tested-inputs|difference-observed|satisfied|
|H007|tf.reduce_prod|refuted-on-tested-inputs|undetermined|undetermined|
|H008|tf.matmul|supported-on-tested-inputs|no-difference-on-tested-inputs|undetermined|
|H009|tf.linalg.det|supported-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|H010|tf.linalg.trace|refuted-on-tested-inputs|no-difference-on-tested-inputs|satisfied|
|H011|tf.cumsum|refuted-on-tested-inputs|undetermined|undetermined|
|H012|tf.math.cumprod|refuted-on-tested-inputs|difference-observed|violated|

## CoSMiT与DLLens结果交叉核对

|组合|候选数|
|---|---:|
|两者均未发现违反/差异|80|
|两者均报告违反/差异|10|
|CoSMiT违反、DLLens因缺输出未决|15|
|CoSMiT违反、DLLens未发现数值差异|3|
|CoSMiT未决、DLLens未发现数值差异|2|

3组为：E030 (tf.clip_by_value)、H005 (torch.cumsum)、H010 (tf.linalg.trace)。不能将28−10当作18组已证实的额外正确检出；独立标签尚未建立。

包结构校验：110组、220个新适配入口、全部冻结文件哈希通过。仅执行6个新增适配器冒烟测试（覆盖复杂数、官方sign梯度及稀疏模式），全部通过；未重新验证公开原测试真实性。
