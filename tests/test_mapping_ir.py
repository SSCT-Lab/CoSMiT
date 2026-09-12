from cosmit.engine.mapping_ir import normalize_candidate


def test_explicit_import_and_transform_parameters_are_preserved():
    ir = normalize_candidate(
        "import tensorflow as tf\ndef f(x):\n return tf.transpose(tf.cast(x,tf.float32),perm=[0,2,1])",
        "tensorflow",
    )
    assert [c.qualified_name for c in ir.calls] == ["tensorflow.transpose", "tensorflow.cast"]
    assert ir.calls[0].keywords == (("perm", "[0, 2, 1]"),)
    assert ir.calls[1].arguments == ("x", "tf.float32")
    assert ir.evidence_kind == "syntax-only"


def test_aliases_must_be_imported_not_guessed():
    ir = normalize_candidate("def f(x):\n return tf.reduce_sum(x)", "tensorflow")
    assert not ir.calls and ir.residual_code


def test_shadowing_blocks_binding_and_dead_code_remains_residual():
    ir = normalize_candidate(
        "import tensorflow as tf\ndef f(tf):\n return tf.reduce_sum(x)", "tensorflow"
    )
    assert not ir.calls and "shadowed-import:tf" in ir.residual_code
    ir = normalize_candidate(
        "import tensorflow as tf\ndef f(x):\n if False:\n  return tf.reduce_sum(x)", "tensorflow"
    )
    assert ir.calls and any(r.startswith("control-flow:") for r in ir.residual_code)


def test_from_import_and_invalid_syntax():
    ir = normalize_candidate("from cupy import squeeze as sq\ndef f(x):\n return sq(x)", "cupy")
    assert ir.calls[0].qualified_name == "cupy.squeeze"
    assert normalize_candidate("def broken(", "cupy").residual_code
