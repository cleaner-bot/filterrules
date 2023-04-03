import typing

from . import ast

Variables = dict[str, type]
Functions = dict[str, tuple[tuple[type, ...], type]]


def lint(
    expr: ast.ExpressionLike,
    variables: Variables,
    functions: Functions,
    untrusted: bool = True,
) -> str | None:
    ctx = LintContext(variables, functions, untrusted)
    try:
        _lint(expr, ctx)
    except RuntimeError as e:
        return typing.cast(str, e.args[0])
    return None


class LintContext(typing.NamedTuple):
    variables: Variables
    functions: Functions
    untrusted: bool


def _lint(expr: ast.ExpressionLike, ctx: LintContext) -> type:
    match expr:
        case ast.Block(inner):
            return _lint(inner, ctx)

        case ast.Constant(value):
            return type(value)

        case ast.Variable(key):
            if key not in ctx.variables:
                raise RuntimeError(f"variable not found: {key!r}")
            return ctx.variables[key]

        case ast.ArrayConstructor(items):
            types = set(_lint(item, ctx) for item in items)
            if len(types) != 1:
                raise RuntimeError(f"unable to determine array type: {types!r}")
            (the_type,) = types
            return list[the_type]  # type: ignore

        case ast.ArrayComprehension(inner):
            left = _lint(inner.left, ctx)
            if left.mro()[0] != list:
                raise RuntimeError(
                    f"cannot use list comprehension on non-lists: {left!r}"
                )
            args: tuple[type, ...] = getattr(left, "__args__", ())
            if not args:
                raise RuntimeError(
                    f"cannot use list comprehension on untyped lists: {left!r}"
                )

            right = _lint(inner.right, ctx)
            body = _lint_binary_operator(inner.operator, args[0], right, ctx)
            return list[body]  # type: ignore

        case ast.BinaryOperation(operator, _, _):
            left = _lint(expr.left, ctx)
            right = _lint(expr.right, ctx)

            return _lint_binary_operator(operator, left, right, ctx)

        case ast.UnaryOperation(operator, _):
            valuetype = _lint(expr.value, ctx)
            match operator:
                case "not":
                    return bool
                case "bnot" | "plus" | "minus":
                    if valuetype != int:
                        raise RuntimeError(
                            f"cannot use {operator} operator on non-integer: "
                            f"{valuetype.__name__!r}"
                        )
                    return int

        case ast.FunctionCall(name, arguments):
            if name not in ctx.functions:
                raise RuntimeError(f"function not found: {name!r}")
            fn = ctx.functions[name]
            if len(arguments) != len(fn[0]):
                raise RuntimeError(
                    f"function has incorrect amount of arguments, "
                    f"got {len(arguments)}, expected {len(fn[0])}"
                )
            argument_types = tuple(_lint(arg, ctx) for arg in arguments)
            if argument_types != fn[0]:
                expected_names = tuple(x.__name__ for x in fn[0])
                argument_type_names = tuple(x.__name__ for x in argument_types)
                raise RuntimeError(
                    f"function has incorrect argument signature, "
                    f"got {argument_type_names}, expected {expected_names}"
                )
            return fn[1]

    raise RuntimeError(f"unknown ast node: {expr}")


def _lint_binary_operator(
    operator: str, left: type, right: type, ctx: LintContext
) -> type:
    match operator:
        case "add" | "multiply":
            if (left, right) in ((int, float), (float, int)):
                return float
            elif left != right:
                raise RuntimeError(
                    f"cannot use {operator} operator on different types: "
                    f"{left.__name__!r} and {right.__name__!r}"
                )
            return left
        case "subtract" | "divide":
            if (left, right) in ((int, float), (float, int)):
                return float
            elif left != right:
                raise RuntimeError(
                    f"cannot use {operator} operator on different types: "
                    f"{left.__name__!r} and {right.__name__!r}"
                )
            elif left not in (int, float):
                raise RuntimeError(
                    f"cannot use {operator} operator on non-numbers: "
                    f"{left.__name__!r}"
                )
            return left
        case "band" | "bor" | "bxor" | "lshift" | "rshift":
            if left != right:
                raise RuntimeError(
                    f"cannot use {operator} operator on different types: "
                    f"{left.__name__!r} and {right.__name__!r}"
                )
            elif left != int:
                raise RuntimeError(
                    f"cannot use {operator} operator on non-integer: "
                    f"{left.__name__!r}"
                )
            return left
        case "pow":
            if ctx.untrusted:
                raise RuntimeError("cannot use pow operator in untrusted code")
            elif left != right:
                raise RuntimeError(
                    f"cannot use pow operator on different types: "
                    f"{left.__name__!r} and {right.__name__!r}"
                )
            elif left not in (int, float):
                raise RuntimeError(
                    f"cannot use pow operator on non-numbers: " f"{left.__name__!r}"
                )
            return left
        case "equals" | "not-equals":
            return bool
        case (
            "greater-than"
            | "greater-than-or-equals"
            | "less-than"
            | "less-than-or-equals"
        ):
            if left != right:
                raise RuntimeError(
                    f"cannot use {operator} operator on different types: "
                    f"{left.__name__!r} and {right.__name__!r}"
                )
            elif left not in (int, float):
                raise RuntimeError(
                    f"cannot use {operator} operator on non-numbers: "
                    f"{left.__name__!r}"
                )
            return bool
        case "and" | "or":
            if left != right:
                raise RuntimeError(
                    f"cannot use {operator} operator on different types: "
                    f"{left.__name__!r} and {right.__name__!r}"
                )
            return right
        case "in":
            if right.mro()[0] != list:
                raise RuntimeError(
                    f"cannot use {operator} operator on non-lists: {right!r}"
                )
            args: tuple[type, ...] = getattr(right, "__args__", ())
            if not args:
                raise RuntimeError(
                    f"cannot use {operator} operator on untyped lists: " f"{right!r}"
                )
            if left != args[0]:
                raise RuntimeError(
                    f"cannot use {operator} operator on different types: "
                    f"{left.__name__!r} and {args[0].__name__!r}"
                )
            return bool

    raise RuntimeError(f"unknown operator: {operator}")
