"""Tests for Pix2Text output normalization."""

import unittest

from app.services.ocr.pix2text_service import Pix2TextService


class Pix2TextServiceTests(unittest.TestCase):
    def test_formula_fragments_are_rendered_as_markdown_latex(self) -> None:
        output = [
            {"type": "text", "text": "Çözünüz:"},
            {"type": "isolated", "text": r"\int_0^1 x^2 dx"},
        ]

        text = Pix2TextService._normalize_output(output)

        self.assertEqual(text, "Çözünüz:\n$$\\int_0^1 x^2 dx$$")
        self.assertEqual(
            Pix2TextService._extract_latex(text),
            r"\int_0^1 x^2 dx",
        )
