"""Controlled source tests for the IntentTester TDL sufficiency audit.

The functions are never used as CoSMiT gold output.  Each adjacent pair changes
one transport-critical clause while keeping the high-level testing goal fixed.
"""

import torch


def test_sum_value_only():
    x = torch.tensor([1, 2, 3], dtype=torch.int32)
    actual = torch.sum(x)
    assert actual.item() == 6


def test_sum_value_and_dtype():
    x = torch.tensor([1, 2, 3], dtype=torch.int32)
    actual = torch.sum(x)
    assert actual.item() == 6
    assert actual.dtype == torch.int64


def test_close_atol_1e5():
    actual = torch.tensor(1.000005, dtype=torch.float32)
    expected = torch.tensor(1.0, dtype=torch.float32)
    torch.testing.assert_close(actual, expected, rtol=0.0, atol=1e-5)


def test_close_atol_1e6():
    actual = torch.tensor(1.0000005, dtype=torch.float32)
    expected = torch.tensor(1.0, dtype=torch.float32)
    torch.testing.assert_close(actual, expected, rtol=0.0, atol=1e-6)


def test_squeeze_unit_axis():
    x = torch.ones((1, 1, 3), dtype=torch.float32)
    actual = torch.squeeze(x, dim=1)
    assert actual.shape == (1, 3)


def test_squeeze_nonunit_axis():
    x = torch.ones((1, 3), dtype=torch.float32)
    actual = torch.squeeze(x, dim=1)
    assert actual.shape == (1, 3)


def test_cross_entropy_class_axis_one():
    logits = torch.tensor(
        [[[4.0, 1.0, -2.0], [1.0, 3.0, 0.5], [-1.0, 0.0, 5.0]]],
        dtype=torch.float32,
    )
    labels = torch.tensor([[0, 1, 2]], dtype=torch.int64)
    actual = torch.nn.functional.cross_entropy(logits, labels, reduction="mean")
    assert actual.item() >= 0.0


def test_cross_entropy_class_axis_last():
    logits = torch.tensor(
        [[[4.0, 1.0, -2.0], [1.0, 3.0, 0.5], [-1.0, 0.0, 5.0]]],
        dtype=torch.float32,
    )
    labels = torch.tensor([[0, 1, 2]], dtype=torch.int64)
    actual = torch.nn.functional.cross_entropy(
        logits.transpose(1, 2), labels, reduction="mean"
    )
    assert actual.item() >= 0.0
