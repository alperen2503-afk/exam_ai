"""Deterministic first-pass mathematics topic classifier."""

from app.models.analysis import Topic


def classify_expression(expression: str) -> Topic:
    """Classify a normalized arithmetic or algebra expression."""
    left = expression.partition("=")[0]
    operators = {operator for operator in "+-*/" if operator in left.lstrip("+-")}
    if any(char.isalpha() for char in left):
        return Topic.ALGEBRA
    if len(operators) > 1:
        return Topic.MIXED_ARITHMETIC
    if "+" in operators:
        return Topic.ADDITION
    if "-" in operators:
        return Topic.SUBTRACTION
    if "*" in operators:
        return Topic.MULTIPLICATION
    if "/" in operators:
        return Topic.DIVISION
    return Topic.UNKNOWN
