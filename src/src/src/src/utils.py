# src/utils.py
"""
Utility functions:
- safe_eval_decimal(expr): evaluate simple arithmetic to Decimal using AST whitelist
- parse_amount_and_pair(text): extract amount, base, quote (defaults amount=1)
- format_price(amount, price, base, quote): professional output with thousand separators

Examples:
  parse_amount_and_pair("1.5 btc to usd") -> (Decimal("1.5"), "BTC", "USD")
  format_price(Decimal("1.5"), Decimal("2000"), "BTC", "USD")
"""
from __future__ import annotations

import ast
import re
from decimal import Decimal, getcontext


# set reasonable precision; adjust if needed
getcontext().prec = 28

_ALLOWED_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Num,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.USub,
    ast.UAdd,
    ast.Pow,  # optional; consider removing if you fear large exponents
    ast.Mod,  # optional
    ast.FloorDiv,  # optional
}

_MAX_EXPR_LEN = 64
_MAX_DEPTH = 10


def safe_eval_decimal(expr: str) -> Decimal:
    """
    Safely evaluate a simple arithmetic expression into Decimal.
    Supports +, -, *, / (and optionally **, %, //) on numeric literals.
    """
    expr = (expr or "").strip()
    if not expr:
        raise ValueError("Empty expression")
    if len(expr) > _MAX_EXPR_LEN:
        raise ValueError("Expression too long")

    node = ast.parse(expr, mode="eval")

    def _check(n: ast.AST, depth: int = 0):
        if depth > _MAX_DEPTH:
            raise ValueError("Expression too deep")
        if type(n) not in _ALLOWED_NODES:
            raise ValueError(f"Disallowed node: {type(n).__name__}")
        for child in ast.iter_child_nodes(n):
            _check(child, depth + 1)

    _check(node)

    def _eval(n: ast.AST) -> Decimal:
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Num):
            return Decimal(str(n.n))
        if isinstance(n, ast.UnaryOp):
            val = _eval(n.operand)
            if isinstance(n.op, ast.UAdd):
                return val
            if isinstance(n.op, ast.USub):
                return -val
        if isinstance(n, ast.BinOp):
            left = _eval(n.left)
            right = _eval(n.right)
            if isinstance(n.op, ast.Add):
                return left + right
            if isinstance(n.op, ast.Sub):
                return left - right
            if isinstance(n.op, ast.Mult):
                return left * right
            if isinstance(n.op, ast.Div):
                # avoid division by zero
                if right == 0:
                    raise ValueError("Division by zero")
                return left / right
            if isinstance(n.op, ast.Pow):
                # limit exponent to avoid DoS
                if right > 8:
                    raise ValueError("Exponent too large")
                return left ** right
            if isinstance(n.op, ast.Mod):
                return left % right
            if isinstance(n.op, ast.FloorDiv):
                if right == 0:
                    raise ValueError("Division by zero")
                return left // right
        raise ValueError("Invalid expression")

    return _eval(node)


_PAIR_RE = re.compile(
    r"""
    ^\s*
    (?:(?P<amount>[-+]?\d+(?:\.\d+)?)\s+)?     # optional amount
    (?P<base>[A-Za-z]{2,10})                   # base symbol
    \s+(?:to|->|/)\s+                          # separator
    (?P<quote>[A-Za-z]{2,10})                  # quote symbol
    \s*$
    """,
    re.VERBOSE | re.IGNORECASE,
)


def parse_amount_and_pair(text: str):
    """
    Parse queries like:
      "eth to usd" -> amount=1, base=ETH, quote=USD
      "1.5 btc to usd" -> amount=1.5, base=BTC, quote=USD
    Raises ValueError on invalid input.
    """
    text = (text or "").strip()
    m = _PAIR_RE.match(text)
    if not m:
        raise ValueError("Invalid query format")
    amt = m.group("amount")
    base = m.group("base").upper()
    quote = m.group("quote").upper()
    amount = Decimal(amt) if amt is not None else Decimal("1")
    return amount, base, quote


def _thousands(n: Decimal) -> str:
    # simple thousand separator for integers; keep decimals intact
    s = f"{n:.8f}".rstrip("0").rstrip(".")
    parts = s.split(".")
    integer = parts[0]
    frac = parts[1] if len(parts) > 1 else None
    integer_fmt = "{:,}".format(int(integer))
    return integer_fmt if frac is None else f"{integer_fmt}.{frac}"


def format_price(amount: Decimal, price: Decimal, base: str, quote: str) -> str:
    """
    Format output like:
      "1.5 BTC = 3,000.00 USD\nprice: 2,000.00 USD/BTC"
    Uses reasonable precision and separators.
    """
    total = (amount * price)
    return (
        f"{amount} {base} = {_thousands(total)} {quote}\n"
        f"price: {_thousands(price)} {quote}/{base}"
)
