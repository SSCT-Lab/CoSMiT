import importlib
import sys
from pathlib import Path

import pytest


@pytest.fixture
def recovery():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark/baselines"))
    yield importlib.import_module("recover_structured_verifier_outputs")
    sys.path.pop(0)


def response(content, finish="stop"):
    return {"choices": [{"finish_reason": finish, "message": {"content": content}}]}


def test_single_final_typed_object_can_be_recovered(recovery):
    text = '<think>private analysis</think>Explanation.\n```json\n{"valid":false,"reason":"shape differs"}\n```'
    assert recovery.recover(response(text), "intenttester-target-api")["valid"] is False


@pytest.mark.parametrize(
    "text,finish",
    [
        (
            '```json\n{"valid":true,"reason":"ok"}\n```\n```json\n{"valid":false,"reason":"no"}\n```',
            "stop",
        ),
        ('```json\n{"valid":"false","reason":"no"}\n```', "stop"),
        ('```json\n{"valid":true,"reason":"ok"}\n```', "length"),
        ('<think>unfinished\n```json\n{"valid":true,"reason":"ok"}\n```', "stop"),
        ('```json\n{"valid":true,"reason":"ok"}\n```\nActually, no.', "stop"),
    ],
)
def test_ambiguous_truncated_or_wrongly_typed_answers_stay_failed(recovery, text, finish):
    with pytest.raises((ValueError, TypeError)):
        recovery.recover(response(text, finish), "intenttester-target-api")
