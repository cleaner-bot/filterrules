import time

import pytest

from filterrules.parser import parse
from filterrules.rule import Rule


def test_untrusted_pow() -> None:
    rule = Rule(parse(b"2 ** 99999999999999"))

    start = time.monotonic()
    with pytest.raises(
        RuntimeError, match=r"pow operation \(\*\*\) is disabled in untrusted mode"
    ):
        rule.evaluate({}, {})
    with pytest.raises(
        RuntimeError, match=r"pow operation \(\*\*\) is disabled in untrusted mode"
    ):
        rule.compile()

    diff = time.monotonic() - start
    assert diff < 1


def test_untrusted_lshift() -> None:
    start = time.monotonic()

    rule = Rule(parse(b"1 << 128"))
    compiled = rule.compile()
    assert rule.evaluate({}, {}) == 1 << 128
    assert compiled({}, {}) == 1 << 128

    rule = Rule(parse(b"1 << 99999999999999"))
    compiled = rule.compile()
    with pytest.raises(RuntimeError, match="lshift operation with too big values"):
        rule.evaluate({}, {})
    with pytest.raises(RuntimeError, match="lshift operation with too big values"):
        compiled({}, {})

    rule = Rule(parse(b"(1 << 128) << 8"))
    compiled = rule.compile()
    with pytest.raises(RuntimeError, match="lshift operation with too big values"):
        rule.evaluate({}, {})
    with pytest.raises(RuntimeError, match="lshift operation with too big values"):
        compiled({}, {})

    diff = time.monotonic() - start
    assert diff < 1


def test_untrusted_string_memory() -> None:
    start = time.monotonic()

    rule = Rule(parse(b"'x' * (1 << 32)"))
    with pytest.raises(
        RuntimeError,
        match="cannot use non-string right-value on a string in untrusted mode",
    ):
        rule.evaluate({}, {})

    # this would use 100kb of ram but could easily be made much much worse
    rule = Rule(parse(b"+".join(b"x" for _ in range(10))))
    compiled = rule.compile()
    with pytest.raises(
        RuntimeError, match="string longer than allowed in untrusted mode"
    ):
        rule.evaluate({"x": "x" * 10_000}, {})
    with pytest.raises(
        RuntimeError, match="string longer than allowed in untrusted mode"
    ):
        compiled({"x": "x" * 10_000}, {})

    diff = time.monotonic() - start
    assert diff < 1
