import typing

from . import ast

Variables = dict[str, typing.Any]
Functions = dict[str, typing.Callable[..., typing.Any]]


def _untrusted_add(a: typing.Any, b: typing.Any) -> typing.Any:
    c = a + b
    if isinstance(c, (str, bytes)) and len(c) >= 65536:
        raise RuntimeError("string longer than allowed in untrusted mode")
    return c


def _untrusted_lshift(a: int, b: int) -> int:
    if b > 128 or a >= (1 << 128):
        raise RuntimeError("lshift operation with too big values")
    return a << b


_TRUSTED_COMPILER = "lambda vars, fns: %s"
_UNTRUSTED_COMPILER = "lambda __untrusted_add, __untrusted_lshift: lambda vars, fns: %s"


class Rule(typing.NamedTuple):
    expr: ast.ExpressionLike
    untrusted: bool = True

    def evaluate(self, variables: Variables, functions: Functions) -> typing.Any:
        ctx = RuleContext(variables, functions, self.untrusted)
        return _evaluate(self.expr, ctx)

    def compile(self) -> typing.Callable[[Variables, Functions], typing.Any]:
        expr = _compile(self.expr, self.untrusted)
        if self.untrusted:
            fn = eval(_UNTRUSTED_COMPILER % expr, {}, {})(
                _untrusted_add, _untrusted_lshift
            )
        else:
            fn = eval(_TRUSTED_COMPILER % expr, {}, {})
        return typing.cast(typing.Callable[[Variables, Functions], typing.Any], fn)


class RuleContext(typing.NamedTuple):
    variables: Variables
    functions: Functions
    untrusted: bool


def _evaluate(expr: ast.ExpressionLike, ctx: RuleContext) -> typing.Any:
    match expr:
        case ast.Block(inner):
            return _evaluate(inner, ctx)

        case ast.Constant(value):
            return value

        case ast.Variable(key):
            return ctx.variables[key]

        case ast.BinaryOperation(operator, _, _):
            left = _evaluate(expr.left, ctx)
            match operator:  # short circuit logic
                case "and":
                    if not left:
                        return left
                case "or":
                    if left:
                        return left

            right = _evaluate(expr.right, ctx)
            if (
                isinstance(left, (str, bytes))
                and not isinstance(right, (str, bytes))
                and ctx.untrusted
            ):
                raise RuntimeError(
                    "cannot use non-string right-value on a string in untrusted mode"
                )

            match operator:
                case "add":
                    r = left + right
                    if (
                        isinstance(r, (str, bytes))
                        and len(r) >= 65536
                        and ctx.untrusted
                    ):
                        raise RuntimeError(
                            "string longer than allowed in untrusted mode"
                        )
                    return r
                case "subtract":
                    return left - right
                case "multiply":
                    return left * right
                case "divide":
                    return left / right
                case "modulo":
                    return left % right
                case "pow":
                    if ctx.untrusted:
                        raise RuntimeError(
                            "pow operation (**) is disabled in untrusted mode"
                        )
                    return left**right
                case "equals":
                    return left == right
                case "not-equals":
                    return left != right
                case "greater-than":
                    return left > right
                case "greater-than-or-equals":
                    return left >= right
                case "less-than":
                    return left < right
                case "less-than-or-equals":
                    return left <= right
                case "and" | "or":
                    return right
                case "band":
                    return left & right
                case "bor":
                    return left | right
                case "bxor":
                    return left ^ right
                case "lshift":
                    if ctx.untrusted and (right > 128 or (left >= 1 << 128)):
                        raise RuntimeError("lshift operation with too big values")
                    return left << right
                case "rshift":
                    return left >> right

        case ast.UnaryOperation(operator, _):
            value = _evaluate(expr.value, ctx)
            match operator:
                case "not":
                    return not value
                case "bnot":
                    return ~value  # type: ignore
                case "plus":
                    return +value  # type: ignore
                case "minus":
                    return -value  # type: ignore

        case ast.FunctionCall(name, arguments):
            args = [_evaluate(arg, ctx) for arg in arguments]
            return ctx.functions[name](*args)

    raise RuntimeError(f"unknown ast node: {expr}")


_binary_operator_map = {
    "add": "+",
    "subtract": "-",
    "multiply": "*",
    "divide": "/",
    "modulo": "%",
    "pow": "**",
    "equals": "==",
    "not-equals": "!=",
    "greater-than": ">",
    "greater-than-or-equals": ">=",
    "less-than": "<",
    "less-than-or-equals": "<=",
    "and": "and",
    "or": "or",
    "band": "&",
    "bor": "|",
    "bxor": "^",
    "lshift": "<<",
    "rshift": ">>",
}
_unaery_operator_map = {"not": "not", "bnot": "~", "plus": "+", "minus": "-"}


def _compile(expr: ast.ExpressionLike, untrusted: bool) -> str:
    match expr:
        case ast.Block(inner):
            return f"({_compile(inner, untrusted)})"

        case ast.Constant(value):
            return repr(value)

        case ast.Variable(key):
            return f"vars[{key!r}]"

        case ast.BinaryOperation(operator, _, _):
            left = _compile(expr.left, untrusted)
            right = _compile(expr.right, untrusted)
            if untrusted:
                if operator == "pow":
                    raise RuntimeError(
                        "pow operation (**) is disabled in untrusted mode"
                    )
                elif operator in ("lshift", "add"):
                    return f"__untrusted_{operator}({left}, {right})"

            return f"{left} {_binary_operator_map[operator]} {right}"

        case ast.UnaryOperation(operator, _):
            value = _compile(expr.value, untrusted)
            return f"{_unaery_operator_map[operator]} {value}"

        case ast.FunctionCall(name, arguments):
            args = ", ".join(_compile(arg, untrusted) for arg in arguments)
            return f"fns[{name!r}]({args})"

    raise RuntimeError(f"unknown ast node: {expr}")
