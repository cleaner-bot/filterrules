import pytest

from filterrules.lexer import Token, lex


@pytest.mark.parametrize(
    ("input", "expected"),
    (
        (b"abcdef", ((Token.NAME, b"abcdef"),)),
        (b"abcdef(", ((Token.NAME, b"abcdef"), (Token.SEPARATOR, b"("))),
        (
            b"abcdef(test)",
            (
                (Token.NAME, b"abcdef"),
                (Token.SEPARATOR, b"("),
                (Token.NAME, b"test"),
                (Token.SEPARATOR, b")"),
            ),
        ),
        (b'"test"', ((Token.STRING, b"test"),)),
        (
            b'ab"test"',
            (
                (Token.NAME, b"ab"),
                (Token.STRING, b"test"),
            ),
        ),
        (
            b"test('test')",
            (
                (Token.NAME, b"test"),
                (Token.SEPARATOR, b"("),
                (Token.STRING, b"test"),
                (Token.SEPARATOR, b")"),
            ),
        ),
        (b"'\\n'", ((Token.STRING, b"\n"),)),
        (b"'it\\'s a test'", ((Token.STRING, b"it's a test"),)),
        (b"whitespace strip test", ((Token.NAME, b"whitespacestriptest"),)),
        (b"'whitespace strip test'", ((Token.STRING, b"whitespace strip test"),)),
        (b"'\\x0a'", ((Token.STRING, b"\n"),)),
        (b"'the st'", ((Token.STRING, b"the st"),)),
        (b"the best", ((Token.NAME, b"thebest"),)),
    ),
)
def test_lexer(input: bytes, expected: tuple[tuple[Token, bytes], ...]) -> None:
    assert tuple(lex(input)) == expected


def test_invalid_escape_sequence() -> None:
    with pytest.raises(SyntaxError, match="invalid hex-escape sequence"):
        tuple(lex(b"'\\xmm'"))
