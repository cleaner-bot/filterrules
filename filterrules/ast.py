from __future__ import annotations

import typing

BinaryOperators = typing.Literal[
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
    "in",
]
UnaryOperators = typing.Literal["not", "plus", "minus", "bnot"]


class Constant(typing.NamedTuple):
    value: bytes | str | int | float


class ArrayConstructor(typing.NamedTuple):
    items: tuple[ExpressionLike, ...]


class ArrayComprehension(typing.NamedTuple):
    body: BinaryOperation


class Variable(typing.NamedTuple):
    name: str


class Block(typing.NamedTuple):
    body: ExpressionLike


class BinaryOperation(typing.NamedTuple):
    operator: BinaryOperators
    left: ExpressionLike
    right: ExpressionLike


class UnaryOperation(typing.NamedTuple):
    operator: UnaryOperators
    value: ExpressionLike


class FunctionCall(typing.NamedTuple):
    name: str
    arguments: tuple[ExpressionLike, ...]


ExpressionLike = (
    Constant
    | Variable
    | Block
    | BinaryOperation
    | UnaryOperation
    | FunctionCall
    | ArrayConstructor
    | ArrayComprehension
)
