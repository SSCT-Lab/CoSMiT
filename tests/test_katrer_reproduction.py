import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "benchmark/public_systems/katrer_reproduction.py"
)
SPEC = importlib.util.spec_from_file_location("katrer_reproduction", MODULE_PATH)
assert SPEC and SPEC.loader
KATRER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = KATRER
SPEC.loader.exec_module(KATRER)

CHECKER_PATH = (
    Path(__file__).resolve().parents[1] / "benchmark/public_systems/katrer_property_check.py"
)
CHECKER_SPEC = importlib.util.spec_from_file_location("katrer_property_check", CHECKER_PATH)
assert CHECKER_SPEC and CHECKER_SPEC.loader
CHECKER = importlib.util.module_from_spec(CHECKER_SPEC)
sys.modules[CHECKER_SPEC.name] = CHECKER
CHECKER_SPEC.loader.exec_module(CHECKER)


class KATRERReproductionTests(unittest.TestCase):
    def test_rejected_sse_retains_usage_and_payload_without_credentials(self) -> None:
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def __iter__(self):
                event = {
                    "choices": [{"delta": {"content": "unfinished"}, "finish_reason": "length"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                }
                return iter([("data: " + json.dumps(event)).encode(), b"data: [DONE]"])

        with (
            patch.object(KATRER.urllib.request, "urlopen", return_value=Response()),
            self.assertRaises(KATRER.RejectedResponse) as caught,
        ):
            KATRER.api_call(
                "https://example.invalid",
                "FAKE-SECRET",
                "test prompt",
                KATRER.ModelConfig("test-model", 0.6, 0.95, 1.0, 20),
                1,
            )
        error = caught.exception
        self.assertEqual(error.reason, "non-stop-termination")
        self.assertEqual(error.response["usage"]["total_tokens"], 30)
        self.assertEqual(error.request_payload["messages"][-1]["content"], "test prompt")
        self.assertNotIn("FAKE-SECRET", json.dumps([error.request_payload, error.response]))

    def test_strip_reasoning_and_extract_reused_test(self) -> None:
        response = """<think>private reasoning</think>
[Reused_Test]
```python
import cupy as cp

def test_sum():
    assert cp.sum(cp.asarray([1, 2])).item() == 3
```
[/Reused_Test]"""
        code = KATRER.clean_python_block(response)
        self.assertNotIn("think", code)
        self.assertIn("import cupy as cp", code)
        self.assertEqual(KATRER.syntax_status(code), ("valid", None))
        self.assertTrue(KATRER.target_binding_status(code, "cupy"))

    def test_judgement_parser_is_strict(self) -> None:
        self.assertEqual(
            KATRER.judgement_value("[ConsistencyAnswer]Consistent[/ConsistencyAnswer]"),
            "consistent",
        )
        self.assertEqual(KATRER.judgement_value("probably consistent"), "undetermined")

    def test_manifest_prompts_build_without_model_call(self) -> None:
        manifest = KATRER.yaml.safe_load(KATRER.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        cases = KATRER.enrich_cases(manifest)
        self.assertEqual(len(cases), 3)
        required = [
            KATRER.ROOT / path
            for case in cases
            for path in [
                case["source_test_path"],
                *(s["path"] for s in case["source_symbols"]),
                *(s["path"] for s in case["target_symbols"]),
            ]
        ]
        if not all(path.is_file() for path in required):
            self.skipTest("optional pinned upstream checkouts are not installed")
        for case in cases:
            prompt, source = KATRER.build_generation_prompt(case, KATRER.ROOT)
            self.assertIn("[TestIntention]", prompt)
            self.assertIn("[TarCodeContexts]", prompt)
            self.assertIn(case["target_library"], prompt)
            compile(source, case["source_test_path"], "exec")

    def test_target_binding_requires_target_import(self) -> None:
        self.assertFalse(KATRER.target_binding_status("import numpy as np\n", "cupy"))
        self.assertTrue(KATRER.target_binding_status("from cupy import fft\n", "cupy"))

    def test_exception_clause_checker_requires_guarded_zero_length_fft(self) -> None:
        good = """import cupy as cp
import pytest
def test_fft():
    with pytest.raises(ValueError):
        cp.fft.fft(cp.array([1]), n=0)
"""
        bad = """import cupy as cp
def test_fft():
    cp.fft.fft(cp.array([1]), n=0)
"""
        self.assertTrue(CHECKER.candidate_clause_check("KATRER-NC-001", good)[0])
        self.assertFalse(CHECKER.candidate_clause_check("KATRER-NC-001", bad)[0])

    def test_audit_negative_controls_are_not_accepted(self) -> None:
        import json

        audit = json.loads(
            (KATRER.ROOT / "benchmark/public_systems/katrer-audit-2026-09-08.json").read_text()
        )
        for case in audit["synthetic_checker_diagnostics"]:
            with self.subTest(case=case["id"]):
                self.assertFalse(
                    CHECKER.candidate_clause_check(case["case_id"], case["synthetic_code"])[0]
                )

    def test_unknown_control_flow_and_shadowing_are_unresolved(self) -> None:
        for code in [
            "import cupy as cp\nimport pytest\ndef test_f(cp):\n with pytest.raises(ValueError):\n  cp.fft.fft([1],0)",
            "import cupy as cp\nimport pytest\ndef test_f():\n cp = fake\n with pytest.raises(ValueError):\n  cp.fft.fft([1],0)",
        ]:
            self.assertFalse(CHECKER.candidate_clause_check("KATRER-NC-001", code)[0])

    def test_stream_completion_and_empty_test_gates(self) -> None:
        for reason in [None, "length", "content_filter"]:
            with self.assertRaises(RuntimeError):
                KATRER.validate_response(
                    {"choices": [{"finish_reason": reason, "message": {"content": "x"}}]}
                )
        for content in ["", None, "<think>unfinished"]:
            with self.assertRaises(RuntimeError):
                KATRER.validate_response(
                    {"choices": [{"finish_reason": "stop", "message": {"content": content}}]}
                )
        for code in [
            "",
            "import cupy",
            "def test_f():\n pass",
            "import pytest\ndef test_f():\n pytest.skip()",
        ]:
            self.assertTrue(KATRER.test_candidate_issues(code))


if __name__ == "__main__":
    unittest.main()
