import pytest

from filterrules.lint import lint
from filterrules.parser import parse


@pytest.mark.parametrize(
    ("input", "expected"),
    (
        (
            b"1 + 'test'",
            "cannot use add operator on different types: 'int' and 'bytes'",
        ),
        (b"1 + 1.0", None),  # type coercion
        (b"'ab' + 'cd'", None),
        (b"1 - 1.0", None),  # type coercion
        (
            b"1 - 'test'",
            "cannot use subtract operator on different types: 'int' and 'bytes'",
        ),
        (b"'test' - 'test'", "cannot use subtract operator on non-numbers: 'bytes'"),
        (b"(1) + 1", None),
        (b"1 - 1", None),
        (
            b"1 | 'test'",
            "cannot use bor operator on different types: 'int' and 'bytes'",
        ),
        (b"1.0 | 1.0", "cannot use bor operator on non-integer: 'float'"),
        (b"1 | 1", None),
        (b"1 ** 1", "cannot use pow operator in untrusted code"),
        (b"1 == 1", None),
        (
            b"1 > 1.0",
            "cannot use greater-than operator on different types: 'int' and 'float'",
        ),
        (
            b"'test' > 'test'",
            "cannot use greater-than operator on non-numbers: 'bytes'",
        ),
        (b"1 > 1", None),
        (b"1 && 1", None),
        (
            b"1 && 'test'",
            "cannot use and operator on different types: 'int' and 'bytes'",
        ),
        (b"!1", None),
        (b"~1", None),
        (b"~'test'", "cannot use bnot operator on non-integer: 'bytes'"),
        (b"test", "variable not found: 'test'"),
        (b"var + 1", None),
        (b"test()", "function not found: 'test'"),
        (b"fn()", "function has incorrect amount of arguments, got 0, expected 1"),
        (b"fn(1, 2)", "function has incorrect amount of arguments, got 2, expected 1"),
        (
            b"fn('test')",
            "function has incorrect argument signature, got ('bytes',), "
            "expected ('int',)",
        ),
        (b"fn(1) & 1", None),
        (b"[]", "unable to determine array type: set()"),
        (b"var ~ [1, 2, 3]", None),
        (
            b"var ~ [1.0]",
            "cannot use in operator on different types: 'int' and 'float'",
        ),
        (b"var ~ var", "cannot use in operator on non-lists: <class 'int'>"),
        (b"var ~ list", "cannot use in operator on untyped lists: <class 'list'>"),
    ),
)
def test_lint(input: bytes, expected: str | None) -> None:
    assert (
        lint(parse(input), {"var": int, "list": list}, {"fn": ((int,), int)})
        == expected
    )


@pytest.mark.parametrize(
    ("input", "expected"),
    (
        (b"1 ** 1", None),
        (
            b"1 ** 'test'",
            "cannot use pow operator on different types: 'int' and 'bytes'",
        ),
        (b"'test' ** 'test'", "cannot use pow operator on non-numbers: 'bytes'"),
    ),
)
def test_trusted_lint(input: bytes, expected: str | None) -> None:
    assert lint(parse(input), {}, {}, untrusted=False) == expected


def test_invalid_ast_lint() -> None:
    assert lint(object(), {}, {}).startswith("unknown ast node: ")  # type: ignore
