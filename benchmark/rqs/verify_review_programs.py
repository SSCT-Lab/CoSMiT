"""Check our AST-specialized review programs against their registered kernels.

Only repository-authored fixture code is executed. Never use this script with
untrusted uploaded Python or with model-generated code.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import kernels
from prepare_review import program
from subjects import probes, subjects

from cosmit.engine.certification import observe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("review_key", type=Path)
    args = parser.parse_args()
    data = json.loads(args.packet.read_text())
    key = {r["candidate_id"]: r["blind_id"] for r in json.loads(args.review_key.read_text())}
    records = {r["blind_id"]: r for r in data["records"]}
    kernel_source = Path(kernels.__file__).read_text()
    checks = 0
    for subject in subjects():
        for candidate in subject.candidates:
            record = records[key[candidate.candidate_id]]
            expected = program(
                kernel_source,
                "target",
                subject.family,
                candidate.origin == "evidence-derived-reference",
            )
            source_expected = program(kernel_source, "source", subject.family, None)
            if record["candidate_code"] != expected or record["source_code"] != source_expected:
                raise ValueError("packet program differs from repository fixture")
            namespace = dict(vars(kernels))
            # exec is restricted to exact, freshly regenerated repository fixtures.
            exec(  # noqa: S102 - only freshly generated repository fixtures, never packet/model code.
                "from __future__ import annotations\n" + source_expected + expected,
                namespace,
            )
            for probe in probes(subject, "random", 8741, 4) + [subject.original]:
                assert observe(namespace["candidate_operation"], probe) == observe(
                    candidate.execute, probe
                )
                assert observe(namespace["source_operation"], probe) == observe(
                    subject.prop.source, probe
                )
                checks += 2
    print(f"{checks} specialized-program comparisons passed")


if __name__ == "__main__":
    main()
