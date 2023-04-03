import enum
import string
import typing


class Token(enum.Enum):
    NAME = enum.auto()
    STRING = enum.auto()
    SEPARATOR = enum.auto()
    OPERATOR = enum.auto()


STRING_CHARS = (b"'", b'"')
ESCAPED_STRINGS = {b"n": b"\n", b"r": b"\r"}
HEX_CHARS = b"0123456789abcdef"
SEPARATOR_CHARS = b"()[]{},"
OPERATOR_CHARS = b"+-*/=!<>&|^~%"
WHITESPACE_CHARS = string.whitespace.encode()


def lex(code: bytes) -> typing.Generator[tuple[Token, bytes], None, None]:
    stream = [code[i : i + 1] for i in range(len(code))]
    buffer: list[bytes] = []
    waiting_for_break = None
    next_escaped = False
    while stream and (char := stream.pop(0)):
        if char in STRING_CHARS and not next_escaped and waiting_for_break is None:
            if buffer:
                yield Token.NAME, b"".join(buffer)
                buffer.clear()
            waiting_for_break = char

        elif char in WHITESPACE_CHARS and waiting_for_break is None:  # strip whitespace
            pass

        elif (
            char in SEPARATOR_CHARS or char in OPERATOR_CHARS
        ) and not waiting_for_break:
            if buffer:
                yield Token.NAME, b"".join(buffer)
                buffer.clear()

            yield Token.SEPARATOR if char in SEPARATOR_CHARS else Token.OPERATOR, char

        elif char == b"\\" and not next_escaped:
            next_escaped = True
            continue

        elif next_escaped and char in ESCAPED_STRINGS:
            buffer.append(ESCAPED_STRINGS[char])

        elif next_escaped and char == b"x":
            char1 = stream.pop(0)
            char2 = stream.pop(0)
            if char1 not in HEX_CHARS or char2 not in HEX_CHARS:
                raise SyntaxError("invalid hex-escape sequence")
            buffer.append(
                ((HEX_CHARS.index(char1) << 4) + HEX_CHARS.index(char2)).to_bytes(
                    1, "big"
                )
            )

        elif char == waiting_for_break and not next_escaped:
            yield Token.STRING, b"".join(buffer)
            buffer.clear()
            waiting_for_break = None

        else:
            buffer.append(char)

        next_escaped = False

    if buffer:
        yield Token.NAME, b"".join(buffer)
