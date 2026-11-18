# 配对统计分析

## 方法与解释
- 分类主比较：全候选正确判定率（与正文 all-candidate accuracy 一致）。未决计为未作出正确判定，不等同于语义错误或支持。
- 配对精确 McNemar（二侧二项检验）比较同一候选上的正确/不正确，分别对行为4项、意图7项、核心消融2项作 Holm 校正。
- 搜索以候选为单位，先平均三个种子的稳定反例率与评估次数，再做二侧候选内标签交换检验。非零差值≤18时完全枚举，否则100000次随机置换并采用加一校正。检验交换性假设，不代表随机抽样的总体因果结论。
- 搜索全部四种确认策略六个配对都报告，按检出与成本两个指标族各自Holm校正。不复验策略不参与稳定反例率检验。
- 差值区间为20000次配对候选重采样百分位95%区间，逐项区间未作多重校正。所有种子随候选一起重采样。
- 另按相同源测试repository/path/function整体交换，作分类结果敏感性检查。这只是相关性分组代理，不声称等于独立API家族。
- F1重采样保留未决口径；满分导致的[1,1]只是退化经验区间，不能当作确定性保证。全候选准确率另给精确二项区间（依赖候选独立假设）。
- 本分析不改变任何标签或预测。意图结果仍为不同检查范围之间的诊断性比较。消融只含Full及两个核心移除项，不把Full自比较当作统计证据。

## 行为基线

|比较（左减右）|差值|95%区间|原始p|Holm p|
|---|---:|---|---:|---:|
|cosmit vs trace-llm|0.1009|[0.0459, 0.1651]|0.00341797|0.00341797|
|cosmit vs direct-llm|0.6514|[0.5596, 0.7431]|1.56701e-20|6.26804e-20|
|cosmit vs dllens|0.1560|[0.0826, 0.2294]|7.62939e-05|0.000152588|
|cosmit vs docter|0.6422|[0.5505, 0.7339]|3.09167e-20|9.27501e-20|

## 意图基线

|比较（左减右）|差值|95%区间|原始p|Holm p|
|---|---:|---|---:|---:|
|cosmit vs trace-llm|0.0826|[0.0183, 0.1468]|0.0224609|0.0449219|
|cosmit vs direct-llm|0.2477|[0.1284, 0.3670]|0.000198039|0.000594118|
|cosmit vs dllens|0.1468|[0.0826, 0.2202]|0.000144958|0.000579834|
|cosmit vs docter|0.3670|[0.2569, 0.4771]|2.29186e-08|1.6043e-07|
|cosmit vs intenttester-source-tdl|0.2202|[0.1376, 0.3028]|3.03239e-06|1.81943e-05|
|cosmit vs intenttester-target-api|-0.1193|[-0.2569, 0.0183]|0.129918|0.129918|
|cosmit vs intenttester-target-tdl-extension|0.2018|[0.1193, 0.2936]|2.74405e-05|0.000137202|

## 核心消融：行为参考

|比较（左减右）|差值|95%区间|原始p|Holm p|
|---|---:|---|---:|---:|
|full vs without-source-obligations|0.1376|[0.0734, 0.2018]|6.10352e-05|0.00012207|
|full vs without-additional-probing|0.0183|[0.0000, 0.0459]|0.5|0.5|

## 搜索稳定反例率

|比较（左减右）|差值|95%区间|原始p|Holm p|
|---|---:|---|---:|---:|
|original-order vs random|-0.0364|[-0.0788, 0.0000]|0.09375|0.28125|
|original-order vs generic-boundary|-0.0727|[-0.1273, -0.0273]|0.0078125|0.046875|
|original-order vs clause-diversity|-0.0455|[-0.0848, -0.0121]|0.03125|0.125|
|random vs generic-boundary|-0.0364|[-0.0697, -0.0121]|0.015625|0.078125|
|random vs clause-diversity|-0.0091|[-0.0212, 0.0000]|0.25|0.28125|
|generic-boundary vs clause-diversity|0.0273|[0.0030, 0.0576]|0.125|0.28125|

## 搜索平均配对次数

|比较（左减右）|差值|95%区间|原始p|Holm p|
|---|---:|---|---:|---:|
|original-order vs random|0.5242|[0.1424, 0.9576]|0.0105699|0.0211398|
|original-order vs generic-boundary|1.0364|[0.5424, 1.5970]|9.9999e-06|5.99994e-05|
|original-order vs clause-diversity|0.5545|[0.1758, 0.9879]|0.00597994|0.0179398|
|random vs generic-boundary|0.5121|[0.2273, 0.8606]|3.99996e-05|0.000199998|
|random vs clause-diversity|0.0303|[0.0091, 0.0576]|0.015625|0.0211398|
|generic-boundary vs clause-diversity|-0.4818|[-0.8212, -0.2061]|7.99992e-05|0.000319997|

## 聚类敏感性

源测试函数分组共 89 组。校正后p见JSON中的source_test_cluster_p_holm。

## 方法参考
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html
