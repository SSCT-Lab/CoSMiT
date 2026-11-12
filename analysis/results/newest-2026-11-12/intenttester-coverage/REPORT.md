# IntentTester判定覆盖率核查

逐条核查冻结计划、两轮补跑、模型原始content、parsed.valid及109组汇总；未调用模型。

|组件|批次数|批次True/False/null|候选True/False/null|
|---|---:|---|---|
|intenttester-source-tdl|268|268/0/0|109/0/0|
|intenttester-target-api|249|115/134/0|26/83/0|
|intenttester-target-tdl-extension|264|262/2/0|107/2/0|

所有原始JSON响应与parsed.valid一致，候选聚合与现行分析一致。未发现null或失败转成确定判断。

提示允许true/false/null，解析器严格接受布尔或null；完整批次中任一false则候选false，全true才true，否则null。当前数据没有null，因此否定优先聚合没有掩盖未决。

覆盖率100%表示109组全部给出确定布尔结果，不表示100%正确、输入覆盖完整或完整测试意图被验证。Source TDL/Target API/Target TDL扩展是验证组件代理，不能将其确定率当成端到端能力。
