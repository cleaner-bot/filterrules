import typing

import pytest

from filterrules.parser import parse
from filterrules.rule import Rule


@pytest.mark.parametrize(
    "input, expected",
    (
        (b"123 + 456", 579),
        (b"(123)", 123),
        (b"0 ~ [0, 1]", True),
        (b"0 ~ [1]", False),
        (b"!0 ~ {[0, 1] == 1}", True),
    ),
)
def test_expression(input: bytes, expected: typing.Any) -> None:
    rule = Rule(parse(input))
    compiled = rule.compile()
    assert rule.evaluate({}, {}) == expected
    assert compiled({}, {}) == expected


def test_variable() -> None:
    rule = Rule(parse(b"true"))
    compiled = rule.compile()
    assert rule.evaluate({"true": True}, {}) is True
    assert compiled({"true": True}, {}) is True


def test_function_call() -> None:
    rule = Rule(parse(b"fn(123)"))
    compiled = rule.compile()
    assert rule.evaluate({}, {"fn": lambda x: x * 2}) == 246
    assert compiled({}, {"fn": lambda x: x * 2}) == 246


@pytest.mark.parametrize(
    "operation",
    (
        "+",
        "-",
        "*",
        "/",
        "%",
        "**",
        "==",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
        "&",
        "|",
        "^",
        "<<",
        ">>",
    ),
)
def test_math(operation: str) -> None:
    rule = Rule(parse(f"456 {operation} 123".encode()), untrusted=False)
    expected = eval(f"456 {operation} 123")
    compiled = rule.compile()
    assert rule.evaluate({}, {}) == expected
    assert compiled({}, {}) == expected


@pytest.mark.parametrize("operation", ("!", "~", "+", "-"))
def test_unary(operation: str) -> None:
    python_operator = "not" if operation == "!" else operation
    rule = Rule(parse(f"{operation} -42069".encode()))
    compiled = rule.compile()
    assert rule.evaluate({}, {}) == eval(f"{python_operator} -42069")
    assert compiled({}, {}) == eval(f"{python_operator} -42069")


def test_and() -> None:
    rule = Rule(parse(b"a() && b()"))
    compiled = rule.compile()

    # test short circuit
    rule.evaluate({}, {"a": lambda: False, "b": lambda: 1 / 0})
    compiled({}, {"a": lambda: False, "b": lambda: 1 / 0})

    assert rule.evaluate({}, {"a": lambda: True, "b": lambda: 1337}) == 1337
    assert compiled({}, {"a": lambda: True, "b": lambda: 1337}) == 1337


def test_or() -> None:
    rule = Rule(parse(b"a() || b()"))
    compiled = rule.compile()

    # test short circuit
    rule.evaluate({}, {"a": lambda: True, "b": lambda: 1 / 0})
    compiled({}, {"a": lambda: True, "b": lambda: 1 / 0})

    assert rule.evaluate({}, {"a": lambda: False, "b": lambda: 1337}) == 1337
    assert compiled({}, {"a": lambda: False, "b": lambda: 1337}) == 1337


def test_unknown_ast() -> None:
    with pytest.raises(RuntimeError, match="unknown ast node: .+"):
        rule = Rule(object)  # type: ignore
        rule.evaluate({}, {})

    with pytest.raises(RuntimeError, match="unknown ast node: .+"):
        rule = Rule(object)  # type: ignore
        rule.compile()


@pytest.mark.parametrize(
    ("input", "expected"),
    (
        (b"1 + 2 * 3", 9),
        (b"10 * 2 + 3", 23),
        (b"(10 * 2) + 3", 23),
        (b"10 * 5 - 3", 47),
        (b"10 * (2 + 3)", 50),
    ),
)
def test_operator_precedence(input: bytes, expected: int) -> None:
    rule = Rule(parse(input))
    compiled = rule.compile()

    assert rule.evaluate({}, {}) == expected
    assert compiled({}, {}) == expected


@pytest.mark.parametrize(
    "input",
    (
        b"{[] == (1 / 0)}",
        b"{[!0] || (1 / 0)}",
        b"{[!1] && (1 / 0)}",
    ),
)
def test_short_circuit_list_comprehension(input: bytes) -> None:
    rule = Rule(parse(input))
    compiled = rule.compile()

    rule.evaluate({}, {})
    compiled({}, {})
