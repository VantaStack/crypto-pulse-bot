"""
utils.py
--------
Parsing, symbol normalization, safe arithmetic via AST,
and output formatting.
"""

import ast
import operator
import re
from decimal import Decimal
from typing import Optional, Dict


# Safe arithmetic evaluator using AST (no eval).
OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.AST) -> Decimal:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Decimal(str(node.value))
    if isinstance(node, ast.Num):  # for Python <3.8 compatibility if needed
        return Decimal(str(node.n))
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        result = OPS[type(node.op)](float(left), float(right))
        return Decimal(str(result))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        operand = _eval_node(node.operand)
        result = OPS[type(node.op)](float(operand))
        return Decimal(str(result))
    if isinstance(node, ast.Expr):
        return _eval_node(node.value)
    raise ValueError("Unsupported expression")


def eval_amount(expr: Optional[str]) -> Decimal:
    """Evaluate arithmetic expression safely. Default amount = 1."""
    if not expr:
        return Decimal("1")
    if not re.fullmatch(r"[0-9\.\s\+\-\*/\(\)]+", expr):
        raise ValueError("Invalid characters in amount expression")
    tree = ast.parse(expr, mode="eval")
    return _eval_node(tree.body)


# Aliases mapping: readable symbols to CoinGecko IDs or fiat ISO codes.
SYMBOLS_ALIAS: Dict[str, str] = {
    # crypto
    "btc": "bitcoin",
    "eth": "ethereum",
    "ltc": "litecoin",
    "xrp": "ripple",
    "ada": "cardano",
    "doge": "dogecoin",
    "sol": "solana",
    "usdt": "tether",
    "usdc": "usd-coin",
    "bnb": "binancecoin",
    "trx": "tron",
    # fiat (ISO)
    "usd": "usd",
    "eur": "eur",
    "cad": "cad",
    "irr": "irr",
    "gbp": "gbp",
    "try": "try",
    "jpy": "jpy",
    "cny": "cny",
}

FIAT_CODES = set(
    ["usd", "eur", "cad", "irr", "gbp", "try", "jpy", "cny"]
)

EXPR_RE = re.compile(
    r"""
    ^\s*
    (?P<expr>[\d\.\s\+\-\*/\(\)]*)\s*
    (?P<base>[A-Za-z]{2,10})\s*
    (?:(?:to|به))?\s*
    (?P<quote>[A-Za-z]{2,10})?
    \s*$
    """,
    re.VERBOSE | re.IGNORECASE,
)


def normalize_symbol(sym: str) -> str:
    return SYMBOLS_ALIAS.get(sym.lower(), sym.lower())


def is_fiat(sym: str) -> bool:
    return sym.lower() in FIAT_CODES


def parse_query(text: str):
    """
    Parse user query like:
      "2 btc to usd", "(1.2 + 0.3) eth to irr", "btc usd"
    Returns dict: {amount_expr:str|None, base:str, quote:str|None} or None.
    """
    m = EXPR_RE.match(text)
    if not m:
        return None
    expr = m.group("expr").strip() or None
    base = m.group("base").lower()
    quote = m.group("quote").lower() if m.group("quote") else None
    return {"amount_expr": expr, "base": base, "quote": quote}


def format_price(amount: Decimal, price: Decimal, base_sym: str, quote_sym: str) -> str:
    """Format conversion output with trimmed decimals."""
    total = amount * price

    def fmt(d: Decimal) -> str:
        s = f"{d:.12f}".rstrip("0").rstrip(".")
        return s

    return f"{fmt(amount)} {base_sym.upper()} ≈ {fmt(total)} {quote_sym.upper()}"
