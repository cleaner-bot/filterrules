
# filterrules

Performant, 100% typed and mypy strict compliant ruleset language, inspired by
[Cloudflare's Ruleset Engine](https://developers.cloudflare.com/ruleset-engine/).

## Usage

```py
from filterrules import Rule, parse


code = parse(b"bot_score > 90")
rule = Rule(code)

print(rule.evaluate({"bot_score": 10}, {}))
print(rule.evaluate({"bot_score": 100}, {}))

# compile to python for near-python performance
compiled = rule.compile()
print(compiled({"bot_score": 100}, {}))
```

To validate if code is valid before executing it, you can use the `lint()`
function to type-check it.

```py
from filterrules import lint, parse


code = parse(b"bot_score > 90")

issue = lint(code, {"bot_score": int}, {})
if issue:  # issue is None if everything is fine
    print("issue", issue)
issue = lint(code, {"bot_score": str}, {})
if issue:  # different types error
    print("issue", issue)

```

## Security considerations

By default, `Rule()` assumes untrusted code and disables certain features.
You can use `Rule(code, untrusted=False)` to enable all features, but you will
be vulnerable to certain DoS attacks.

For untrusted code, you should limit the length of code passed to `parse()` to
prevent memory exhaustion attacks or other issues.

`rule.evaluate()` runs in linear time O(n), assuming all called foreign
functions are also linear time.

Possible DoS payloads blocked by `untrusted=True` (the default):

- `1 << 99999999999999`
- `2 ** 99999999999999`
- `"x" * (1 << 128)` (this is a linter error too, but executes fine with untrusted=False)
