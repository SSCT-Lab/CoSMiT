# 第一批实验扩充清单

30 条公开 counterpart，15 个家族，两个迁移方向。只完成代码检查与选择，未执行框架或模型。

| ID | 家族 | 源 API | 方向 | 参数 |
| --- | --- | --- | --- | --- |
| E001 | add | torch.add | pytorch-to-tensorflow | input, other |
| E002 | add | tf.add | tensorflow-to-pytorch | x, y |
| E003 | subtract | torch.sub | pytorch-to-tensorflow | input, other |
| E004 | subtract | tf.subtract | tensorflow-to-pytorch | x, y |
| E005 | multiply | torch.mul | pytorch-to-tensorflow | input, other |
| E006 | multiply | tf.multiply | tensorflow-to-pytorch | x, y |
| E007 | divide | torch.div | pytorch-to-tensorflow | input, other |
| E008 | divide | tf.divide | tensorflow-to-pytorch | x, y |
| E009 | maximum | torch.maximum | pytorch-to-tensorflow | input, other |
| E010 | maximum | tf.maximum | tensorflow-to-pytorch | x, y |
| E011 | minimum | torch.minimum | pytorch-to-tensorflow | input, other |
| E012 | minimum | tf.minimum | tensorflow-to-pytorch | x, y |
| E013 | power | torch.pow | pytorch-to-tensorflow | input, exponent |
| E014 | power | tf.math.pow | tensorflow-to-pytorch | x, y |
| E015 | atan2 | torch.atan2 | pytorch-to-tensorflow | input, other |
| E016 | atan2 | tf.atan2 | tensorflow-to-pytorch | y, x |
| E017 | reshape | torch.reshape | pytorch-to-tensorflow | input, shape |
| E018 | reshape | tf.reshape | tensorflow-to-pytorch | tensor, shape |
| E019 | transpose | torch.transpose | pytorch-to-tensorflow | input, dim0, dim1 |
| E020 | transpose | tf.transpose | tensorflow-to-pytorch | a, perm, conjugate |
| E021 | squeeze | torch.squeeze | pytorch-to-tensorflow | input, dim |
| E022 | squeeze | tf.squeeze | tensorflow-to-pytorch | input, axis |
| E023 | expand_dims | torch.unsqueeze | pytorch-to-tensorflow | input, dim |
| E024 | expand_dims | tf.expand_dims | tensorflow-to-pytorch | input, axis |
| E025 | concat | torch.concat | pytorch-to-tensorflow | tensors, dim |
| E026 | concat | tf.concat | tensorflow-to-pytorch | values, axis |
| E027 | stack | torch.stack | pytorch-to-tensorflow | tensors, dim |
| E028 | stack | tf.stack | tensorflow-to-pytorch | values, axis |
| E029 | clip | torch.clip | pytorch-to-tensorflow | input, min, max |
| E030 | clip | tf.clip_by_value | tensorflow-to-pytorch | t, clip_value_min, clip_value_max |

每条代码位置、哈希、调用、适配要求和边界说明见 candidates.json；输入域与 64 输入分层设计见 input-design.json。

当前名单以新增实验覆盖为目的；并未根据执行失败筛选。Tensor 方法、别名和包装层另列在 selection-inventory.json，不计作新增家族。
