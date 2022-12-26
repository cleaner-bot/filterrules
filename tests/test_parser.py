import pytest

from filterrules import ast
from filterrules.parser import parse


@pytest.mark.parametrize(
    ("input", "expected"),
    (
        (b"true", ast.Variable("true")),
        (b"(true)", ast.Block(ast.Variable("true"))),
        (b"1 + 2", ast.BinaryOperation("add", ast.Constant(1), ast.Constant(2))),
        (
            b"1 + 2 + 3",
            ast.BinaryOperation(
                "add",
                ast.Constant(1),
                ast.BinaryOperation("add", ast.Constant(2), ast.Constant(3)),
            ),
        ),
        (b"1 << 32", ast.BinaryOperation("lshift", ast.Constant(1), ast.Constant(32))),
        (
            b"true && true",
            ast.BinaryOperation("and", ast.Variable("true"), ast.Variable("true")),
        ),
        (b"!true", ast.UnaryOperation("not", ast.Variable("true"))),
        (b"~true", ast.UnaryOperation("bnot", ast.Variable("true"))),
        (b"+true", ast.UnaryOperation("plus", ast.Variable("true"))),
        (b"'string'", ast.Constant(b"string")),
        (
            b"1 && !2",
            ast.BinaryOperation(
                "and", ast.Constant(1), ast.UnaryOperation("not", ast.Constant(2))
            ),
        ),
    ),
)
def test_parser(input: bytes, expected: ast.ExpressionLike) -> None:
    assert tuple(parse(input)) == expected


def test_invalid_separator() -> None:
    with pytest.raises(
        SyntaxError, match=r"expected closing SEPARATOR, expected b'\)', not b'\]'"
    ):
        parse(b"(1]'")

    with pytest.raises(SyntaxError, match=r"unexpected b'\)' \(Token.SEPARATOR\)"):
        parse(b")")


def test_invalid_functioncall() -> None:
    with pytest.raises(
        SyntaxError, match="must be a NAME before a function call, not Token.STRING"
    ):
        parse(b"'test'()")

    with pytest.raises(
        SyntaxError, match=r"unexpected SEPARATOR, expected , or \), not b']'"
    ):
        parse(b"test('test']")


def test_invalid_operator() -> None:
    with pytest.raises(SyntaxError, match="unknown OPERATOR: b'&&&&'"):
        parse(b"a &&&& b")


def test_invalid_code() -> None:
    with pytest.raises(SyntaxError, match="expected OPERATOR, not Token.STRING"):
        parse(b"test'abcdef'")
