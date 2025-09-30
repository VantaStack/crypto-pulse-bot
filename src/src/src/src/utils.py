# src/utils.py
"""
Safe parsing, numeric evaluation and formatting utilities.

Principles:
- All financial math uses Decimal with a fixed context.
- Numeric expressions are evaluated via AST with a strict whitelist of nodes.
- Parsing accepts common user forms like:
    "1.2 ETH to USD"
    "eth to usd"         -> amount defaults to 1
    "(1.2 + 0.3) eth to usd"
    "100 usd btc"        -> fallback: last token is quote
- Errors raise ValueError with a clear message (handlers can catch and localize).
- Formatting produces thousand separators and trims trailing zeros.
"""
from __future__ import annotations

import ast
import re
from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from typing import Tuple

# Decimal context: high precision for intermediate ops, banking rounding
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_EVEN

# Allowed AST node types for safe numeric expressions
_ALLOWED_BINOPS = {
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
}
_ALLOWED_UNARYOPS = {ast.UAdd, ast.USub}
_ALLOWED_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant, ast.Tuple, ast.Subscript, ast.Load, ast.Name)

_MAX_EXPONENT = 10

_SYMBOL_RE = re.compile(r"^[A-Za-z]{1,10}$")


def safe_eval_decimal(expr: str) -> Decimal:
    """
    Safely evaluate a numeric expression and return Decimal.
    Supports + - * / % ** and unary ops and parentheses.
    Raises ValueError on disallowed constructs or invalid input.
    """
    if not expr or not expr.strip():
        raise ValueError("Empty expression")

    try:
        node = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Syntax error in expression: {e}") from e

    return _eval_node(node.body)


def _eval_node(node: ast.AST) -> Decimal:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        raise ValueError("Only numeric constants are allowed")
    if isinstance(node, ast.Num):  # py<3.8 fallback
        return Decimal(str(node.n))

    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
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
            if right == Decimal("0"):
                raise ValueError("Division by zero")
            return left / right
        if op is ast.Mod:
            if right == Decimal("0"):
                raise ValueError("Modulo by zero")
            return left % right
        if op is ast.Pow:
            try:
                exp = int(right)
            except Exception:
                raise ValueError("Exponent must be an integer")
            if abs(exp) > _MAX_EXPONENT:
                raise ValueError("Exponent too large")
            return left ** exp

    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        val = _eval_node(node.operand)
        if isinstance(node.op, ast.USub):
            return -val
        return val

    raise ValueError("Unsupported expression")


def _split_to_left_right(text: str) -> Tuple[str, str]:
    """
    Split user text into left (amount+base) and right (quote) by ' to ' (case-insensitive).
    If ' to ' not present, fallback: last token is quote.
    """
    if " to " in text.lower():
        left, right = re.split(r"\s+to\s+", text, flags=re.IGNORECASE, maxsplit=1)
        return left.strip(), right.strip()
    tokens = text.strip().split()
    if len(tokens) < 2:
        raise ValueError("Invalid input: expected '<amount> <symbol> to <quote>'")
    return " ".join(tokens[:-1]).strip(), tokens[-1].strip()


def parse_amount_and_pair(text: str) -> Tuple[Decimal, str, str]:
    """
    Parse user-friendly input and return (amount: Decimal, base_symbol: UPPER, quote_symbol: UPPER).

    Raises ValueError on invalid formats.
    """
    if not text or not text.strip():
        raise ValueError("Empty query")

    left, right = _split_to_left_right(text)

    left_tokens = left.split()
    if not left_tokens:
        raise ValueError("Invalid left-hand side")

    maybe_sym = left_tokens[-1]
    if _SYMBOL_RE.match(maybe_sym):
        base_sym = maybe_sym.upper()
        expr = " ".join(left_tokens[:-1]) or "1"
    else:
        raise ValueError("Base symbol missing or invalid")

    quote = right.upper()
    if not _SYMBOL_RE.match(quote):
        raise ValueError("Quote symbol missing or invalid")

    amt = safe_eval_decimal(expr)

    if amt < Decimal("0"):
        raise ValueError("Amount must be non-negative")

    return amt, base_sym, quote


def _quantize_for_display(d: Decimal, max_decimals: int = 8) -> Decimal:
    """
    Quantize Decimal for display: if integer keep as-is, otherwise quantize to max_decimals.
    """
    if d == d.to_integral():
        return d
    q = Decimal(1).scaleb(-max_decimals)  # 10^-max_decimals
    return d.quantize(q)


def _thousand_sep(s: str) -> str:
    """
    Insert comma as thousand separator for integer part, keep fractional part intact.
    """
    if "." not in s:
        int_part = s
        frac = ""
    else:
        int_part, frac = s.split(".", 1)
        frac = "." + frac
    sign = ""
    if int_part.startswith("-"):
        sign = "-"
        int_part = int_part[1:]
    int_part_with_commas = "{:,}".format(int(int_part)) if int_part else "0"
    return f"{sign}{int_part_with_commas}{frac}"


def format_price(amount: Decimal, price: Decimal, base_sym: str, quote_sym: str, max_decimals: int = 8) -> str:
    """
    Format conversion result:
      "<amount> BASE ≈ <total> QUOTE"
    Thousand separators for readability; trailing zeros trimmed.
    """
    if amount is None or price is None:
        raise ValueError("Amount and price are required")

    total = (amount * price)
    amt_q = _quantize_for_display(amount, max_decimals)
    total_q = _quantize_for_display(total, max_decimals)

    def dec_to_str(d: Decimal) -> str:
        s = format(d.normalize(), "f")
        s = s.rstrip("0").rstrip(".") if "." in s else s
        return _thousand_sep(s)

    return f"{dec_to_str(amt_q)} {base_sym} ≈ {dec_to_str(total_q)} {quote_sym}"
