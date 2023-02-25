import typing

from . import ast
from .lexer import Token, lex


def parse(code: bytes) -> ast.ExpressionLike:
    lexed = list(lex(code))
    return _parse(lexed, 0)


_unary_names: dict[bytes, typing.Literal["not", "plus", "minus", "bnot"]] = {
    b"!": "not",
    b"~": "bnot",
    b"+": "plus",
    b"-": "minus",
}
_operator_names: dict[
    bytes,
    typing.Literal[
        "add",
        "subtract",
        "multiply",
        "divide",
        "modulo",
        "pow",
        "equals",
        "not-equals",
        "greater-than",
        "greater-than-or-equals",
        "less-than",
        "less-than-or-equals",
        "and",
        "or",
        "band",
        "bor",
        "bxor",
        "lshift",
        "rshift",
    ],
] = {
    b"+": "add",
    b"-": "subtract",
    b"*": "multiply",
    b"/": "divide",
    b"%": "modulo",
    b"**": "pow",
    b"==": "equals",
    b"!=": "not-equals",
    b">": "greater-than",
    b">=": "greater-than-or-equals",
    b"<": "less-than",
    b"<=": "less-than-or-equals",
    b"&&": "and",
    b"||": "or",
    b"&": "band",
    b"|": "bor",
    b"^": "bxor",
    b"<<": "lshift",
    b">>": "rshift",
}
_closing_separators = {b"(": b")", b"[": b"]"}


def _parse(
    lex: list[tuple[Token, bytes]], dept: int, parse_expresion: bool = True
) -> ast.ExpressionLike:
    if dept > 100:
        raise SyntaxError("too deeply nested code")

    first_type, first_value = lex.pop(0)
    node: ast.ExpressionLike
    match first_type:
        case Token.NAME:
            value = first_value.decode()
            if value.isdigit():
                node = ast.Constant(int(value))
            else:
                try:
                    node = ast.Constant(float(value))
                except ValueError:
                    node = ast.Variable(value)
        case Token.STRING:
            node = ast.Constant(first_value)
        case Token.SEPARATOR if first_value in b"([":
            node = ast.Block(_parse(lex, dept + 1))
            second_type, second_value = lex.pop(0)
            expected = _closing_separators[first_value]
            # if second_type != Token.SEPARATOR:
            #     raise SyntaxError(f"expected closing SEPARATOR, not {second_type}")
            if expected != second_value:
                raise SyntaxError(
                    f"unexpected closing SEPARATOR, expected {expected!r}, "
                    f"not {second_value!r}"
                )
        case Token.OPERATOR if first_value in b"!~+-":
            node = ast.UnaryOperation(
                _unary_names[first_value], _parse(lex, dept + 1, False)
            )
        case _:
            raise SyntaxError(f"unexpected {first_value!r} ({first_type})")

    if not lex or not parse_expresion:
        return node

    while lex and lex[0][0] == Token.SEPARATOR:
        if lex[0][1] != b"(":
            return node
        lex.pop(0)
        if first_type != Token.NAME:
            raise SyntaxError(
                f"must be a NAME before a function call, not {first_type}"
            )
        args = []
        if lex[0] == (Token.SEPARATOR, b")"):
            lex.pop(0)
        else:
            while lex:
                arg = _parse(lex, dept + 1)
                args.append(arg)
                comma_type, comma_value = lex.pop(0)
                # if comma_type != Token.SEPARATOR:
                #     raise SyntaxError(f"expected SEPARATOR, not {comma_type}")
                if comma_value == b")":
                    break
                elif comma_value != b",":
                    raise SyntaxError(
                        f"unexpected SEPARATOR, expected , or ), not {comma_value!r}"
                    )

        node = ast.FunctionCall(first_value.decode(), tuple(args))

    if not lex:
        return node

    next_type, next_value = lex[0]
    if next_type == Token.OPERATOR:
        operator_buffer: list[bytes] = []
        while lex[0][0] == Token.OPERATOR and (
            not operator_buffer or lex[0][1] not in b"!~+-"
        ):
            operator_buffer.append(lex.pop(0)[1])

        operator = b"".join(operator_buffer)
        if operator not in _operator_names:
            raise SyntaxError(f"unknown OPERATOR: {operator!r}")

        right = _parse(lex, dept + 1)
        # make operations in the order left to right, instead of
        # right to left
        # eg 1 + 2 + 3 is add(add(1, 2), 3) instead of add(1, add(2, 3))
        if isinstance(right, ast.BinaryOperation):
            return ast.BinaryOperation(
                right.operator,
                ast.BinaryOperation(_operator_names[operator], node, right.left),
                right.right,
            )
        return ast.BinaryOperation(_operator_names[operator], node, right)

    else:
        raise SyntaxError(f"expected OPERATOR, not {next_type}")
