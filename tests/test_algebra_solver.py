"""Tests for safe worksheet expression solving."""

import unittest

from app.solver.algebra_solver import MathExpressionError, parse_and_solve


class AlgebraSolverTests(unittest.TestCase):
    def test_blank_division_is_solved(self) -> None:
        solved = parse_and_solve("15 ÷ 5 =")
        self.assertEqual(str(solved.expected_value), "3")
        self.assertIsNone(solved.student_answer)

    def test_ocr_symbol_variants_are_normalized(self) -> None:
        solved = parse_and_solve("3 x 8 = 24")
        self.assertEqual(solved.expression, "3*8=24")

    def test_unsafe_python_is_rejected(self) -> None:
        with self.assertRaises(MathExpressionError):
            parse_and_solve("__import__('os')=1")
