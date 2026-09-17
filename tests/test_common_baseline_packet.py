import importlib
import sys
from pathlib import Path

import pytest


@pytest.fixture
def modules():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark/baselines"))
    yield importlib.import_module("build_common_packet"), importlib.import_module("run_experiment")
    sys.path.pop(0)


def test_primitive_and_composite_target_registration(modules):
    build, _ = modules
    assert build.target_api("def f(x):\n return 1 / x") == "torch.Tensor.__rtruediv__"
    assert build.target_api("def f(x):\n return tf.exp(x) - 1") == "tf.exp"
    assert (
        build.target_api("def f(x):\n return tf.where(x >= 0, tf.floor(x), tf.floor(x)+1)")
        == "tf.where"
    )
    with pytest.raises(ValueError):
        build.target_api("def f(x):\n return x")


def test_invalid_source_assumption_cannot_be_positive(modules):
    _, runner = modules
    states = runner.summarize(
        {
            "status": "completed",
            "records": [{"status": "invalid-source-assumption", "input_index": 0, "repeat": 0}],
        }
    )
    assert set(states.values()) == {"invalid-source-assumption"}
