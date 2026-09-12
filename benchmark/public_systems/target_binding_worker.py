"""Instrument selected simplejson entry points while executing candidate pytest tests."""

from __future__ import annotations

import functools
import json
import sys
from collections import Counter

import pytest
import simplejson

calls: Counter[str] = Counter()


def wrap(owner: object, name: str, label: str) -> None:
    original = getattr(owner, name)

    @functools.wraps(original)
    def tracked(*args: object, **kwargs: object) -> object:
        calls[label] += 1
        return original(*args, **kwargs)

    setattr(owner, name, tracked)


class Collection:
    count = 0

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.count = len(session.items)


def main() -> None:
    for name in ["loads", "load", "dumps", "dump"]:
        wrap(simplejson, name, name)
    wrap(simplejson.JSONDecoder, "decode", "JSONDecoder.decode")
    wrap(simplejson.JSONEncoder, "encode", "JSONEncoder.encode")
    collection = Collection()
    code = pytest.main(["-q", "-p", "no:cacheprovider", sys.argv[1]], plugins=[collection])
    print(
        "COSMIT_BINDING_JSON="
        + json.dumps(
            {
                "pytest_exit_code": int(code),
                "tests_collected": collection.count,
                "target_calls": dict(calls),
                "target_version": simplejson.__version__,
            }
        )
    )


if __name__ == "__main__":
    main()
