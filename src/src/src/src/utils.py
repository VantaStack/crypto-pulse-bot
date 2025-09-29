# src/utils.py
from __future__ import annotations
import ast
from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from typing import Tuple

getcontext().prec = 28
getcontext().rounding = ROUND_HALF_EVEN

_ALLOWED_OPS = {
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.Mod,
}

def safe_eval_decimal(expr: str) -> Decimal:
    """
    Evaluate a numeric expression safely and return Decimal.
    Supports + - * / % ** and parentheses. Rejects names, calls, attributes.
    """
    node = ast.parse(expr, mode="eval")
    return _eval_node(node.body)

def _eval_node(node: ast.AST) -> Decimal:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Decimal(str(node.value))
    if isinstance(node, ast.Num):  # py <3.8 fallback
        return Decimal(str(node.n))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op = type(node.op)
        if op is ast.Add:
            return left + right
        if op is ast.Sub:
            return left - right
        if op is ast.Mult:
            return left * right
        if op is ast.Div:
            return left / right
        if op is ast.Mod:
            return left % right
        if op is ast.Pow:
            # limit exponent size to avoid huge numbers
            if abs(int(right)) > 10:
                raise ValueError("Exponent too large")
            return left ** int(right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        val = _eval_node(node.operand)
        if isinstance(node.op, ast.USub):
            return -val
        if isinstance(node.op, ast.UAdd):
            return val
    raise ValueError("Unsupported expression")

def parse_amount_and_pair(text: str) -> Tuple[Decimal, str, str]:
    """
    Parse inputs like:
      "1.2 ETH to USD"
      "(1.2 ETH + 0.3 ETH) to USD"
      "100 usd to btc"
    Return: (amount_decimal, base_symbol, quote_symbol)
    """
    parts = text.strip().lower().replace(",", " ").split()
    if " to " in text.lower():
        left, right = text.lower().split(" to ", 1)
    else:
        # fallback: last token is quote
        tokens = text.strip().split()
        if len(tokens) < 2:
            raise ValueError("Invalid input")
        left = " ".join(tokens[:-1])
        right = tokens[-1]

    # Try to extract symbol tokens (last word in left might be symbol)
    left = left.strip()
    tokens = left.split()
    if not tokens:
        raise ValueError("Invalid input")

    # If last token is alphabetic symbol (like eth, btc), separate it
    maybe_sym = tokens[-1]
    expr = left
    base_sym = ""
    if maybe_sym.isalpha():
        base_sym = maybe_sym
        expr = " ".join(tokens[:-1]) or "1"
    else:
        # default symbol is empty
        base_sym = ""

    # Evaluate numeric expression in expr
    amt = safe_eval_decimal(expr)
    quote_sym = right.strip()
    if not quote_sym.isalpha():
        # support currencies like usd, eur. If not pure alpha, keep as-is
        pass

    if not base_sym:
        # If user provided only amount and quote, assume base is USD fallback
        raise ValueError("Base symbol missing")

    return amt, base_sym.upper(), quote_sym.upper()

def format_price(amount: Decimal, price: Decimal, base_sym: str, quote_sym: str) -> str:
    """
    Nicely format the conversion result with thousand separators and trimmed decimals.
    """
    total = (amount * price).normalize()
    def fmt(d: Decimal) -> str:
        # represent with up to 8 decimal places, trim trailing zeros
        q = Decimal("0.00000001")
        d = d.quantize(q) if d != d.to_integral() else d
        s = f"{d:,f}"
        # Python's formatting uses commas; replace with thin-space if desired
        return s.rstrip("0").rstrip(".")
    return f"{fmt(amount)} {base_sym} ≈ {fmt(total)} {quote_sym}"
