import pytest

from filterrules.parser import parse
from filterrules.rule import Rule


def test_simple_rule() -> None:
    rule = Rule(parse(b"true"))
    compiled = rule.compile()
    assert rule.evaluate({"true": True}, {}) is True
    assert compiled({"true": True}, {}) is True


def test_math_rule() -> None:
    rule = Rule(parse(b"123 + 456"))
    compiled = rule.compile()
    assert rule.evaluate({}, {}) == 579
    assert compiled({}, {}) == 579


def test_block() -> None:
    rule = Rule(parse(b"(123)"))
    compiled = rule.compile()
    assert rule.evaluate({}, {}) == 123
    assert compiled({}, {}) == 123


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
    compiled = rule.compile()
    assert rule.evaluate({}, {}) == eval(f"456 {operation} 123")
    assert compiled({}, {}) == eval(f"456 {operation} 123")


@pytest.mark.parametrize("operation", ("not", "~", "+", "-"))
def test_unary(operation: str) -> None:
    op = "!" if operation == "not" else operation
    rule = Rule(parse(f"{op} -42069".encode()))
    compiled = rule.compile()
    assert rule.evaluate({}, {}) == eval(f"{operation} -42069")
    assert compiled({}, {}) == eval(f"{operation} -42069")


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


def test_array_in() -> None:
    rule = Rule(parse(b"a ~ [0, 1]"))
    compiled = rule.compile()

    assert rule.evaluate({
        "a": 1,
    }, {}) is True
    assert compiled({
        "a": 1,
    }, {}) is True

    assert rule.evaluate({
        "a": 2,
    }, {}) is False
    assert compiled({
        "a": 2,
    }, {}) is False
