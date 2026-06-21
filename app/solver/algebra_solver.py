"""Safe arithmetic evaluation and elementary equation assessment.

The module name is retained as the future entry point for SymPy-backed
algebra. Numeric worksheet expressions are evaluated without ``eval``.
"""

import ast
from dataclasses import dataclass
from fractions import Fraction
import operator
import re
from typing import Callable


class MathExpressionError(ValueError):
    """Raised when an expression is unsupported or unsafe."""


@dataclass(frozen=True, slots=True)
class SolvedExpression:
    """Parsed worksheet expression and its mathematically correct answer."""

    expression: str
    left_expression: str
    student_answer: str | None
    expected_value: Fraction
    steps: tuple[str, ...]


_BINARY_OPERATORS: dict[type[ast.operator], Callable[[Fraction, Fraction], Fraction]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def normalize_math_text(text: str) -> str:
    """Normalize common OCR and Unicode variants without guessing answers."""
    normalized = re.sub(r"^\s*\d+\s*[\).:-]\s*", "", text.strip())
    replacements = {
        "×": "*",
        "✕": "*",
        "·": "*",
        "÷": "/",
        "−": "-",
        "–": "-",
        "—": "-",
        "＝": "=",
        "：": ":",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"\s+", "", normalized)
    normalized = re.sub(r"(?<=\d)[xX](?=\d)", "*", normalized)
    normalized = re.sub(r"(?<=\d)[sS](?=\d)", "/", normalized)
    normalized = normalized.replace(":", "/")
    return normalized


def parse_and_solve(text: str) -> SolvedExpression:
    """Parse a numeric worksheet row such as ``15 / 5 = 3`` or ``15/5=``."""
    expression = normalize_math_text(text)
    if expression.count("=") > 1:
        raise MathExpressionError("İfadede birden fazla eşittir işareti var.")

    left, separator, right = expression.partition("=")
    if not separator:
        raise MathExpressionError("Öğrenci cevabını ayıran eşittir işareti bulunamadı.")
    if not left or not re.fullmatch(r"[0-9+\-*/().]+", left):
        raise MathExpressionError("Bu ifade henüz güvenli sayısal ifade olarak ayrıştırılamıyor.")

    expected = _evaluate(left)
    student_answer = right or None
    if student_answer is not None and not re.fullmatch(r"[+\-]?(?:\d+(?:[.,]\d+)?|\d+/\d+)", student_answer):
        raise MathExpressionError("Öğrenci cevabı güvenilir biçimde okunamadı.")

    readable = left.replace("*", " × ").replace("/", " ÷ ")
    result_text = format_fraction(expected)
    steps = (
        f"İşlem: {readable}",
        f"İşlem önceliği uygulanır ve sonuç {result_text} bulunur.",
    )
    return SolvedExpression(expression, left, student_answer, expected, steps)


def parse_answer(answer: str) -> Fraction:
    """Convert an OCR answer to an exact rational value."""
    value = answer.replace(",", ".")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise MathExpressionError("Öğrenci cevabı sayıya dönüştürülemedi.") from exc


def format_fraction(value: Fraction) -> str:
    """Format an exact value without floating-point rounding artifacts."""
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _evaluate(expression: str) -> Fraction:
    if len(expression) > 200:
        raise MathExpressionError("İfade güvenli uzunluk sınırını aşıyor.")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise MathExpressionError("Matematiksel ifade ayrıştırılamadı.") from exc
    return _evaluate_node(tree.body, depth=0)


def _evaluate_node(node: ast.AST, depth: int) -> Fraction:
    if depth > 20:
        raise MathExpressionError("İfade güvenli derinlik sınırını aşıyor.")
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        if abs(node.value) > 10**12:
            raise MathExpressionError("Sayı güvenli büyüklük sınırını aşıyor.")
        return Fraction(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate_node(node.operand, depth + 1)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left, depth + 1)
        right = _evaluate_node(node.right, depth + 1)
        if isinstance(node.op, ast.Div) and right == 0:
            raise MathExpressionError("Sıfıra bölme tanımsızdır.")
        return _BINARY_OPERATORS[type(node.op)](left, right)
    raise MathExpressionError("Desteklenmeyen veya güvenli olmayan ifade.")
