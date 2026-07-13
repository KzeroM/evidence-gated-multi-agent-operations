"""Regression tests for repository validation and public-safety checks."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "validate.py"
SPEC = importlib.util.spec_from_file_location("repository_validator", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


class TemplateValidationTests(unittest.TestCase):
    def test_standalone_templates_match_their_schemas(self) -> None:
        self.assertEqual(VALIDATOR.validate_standalone_templates(), [])


class SanitizationTests(unittest.TestCase):
    def findings(self, text: str) -> list[str]:
        return VALIDATOR.sanitization_findings("fixture.txt", text)

    def test_allows_fictional_public_identifiers(self) -> None:
        text = "Contact reviewer" + "@" + "example.org at 192.0.2.20."
        self.assertEqual(self.findings(text), [])

    def test_documentation_address_is_recognized_before_sentence_period(self) -> None:
        match = VALIDATOR.IPV4_RE.search("Use 192.0.2.20.")
        self.assertIsNotNone(match)
        self.assertTrue(VALIDATOR._allowed_ipv4(match.group(0)))

    def test_rejects_non_example_email(self) -> None:
        text = "Contact operator" + "@" + "company.invalid."
        self.assertTrue(any("non-example email" in item for item in self.findings(text)))

    def test_rejects_non_documentation_address(self) -> None:
        text = "Resolver " + ".".join(("8", "8", "8", "8"))
        self.assertTrue(any("non-documentation IPv4" in item for item in self.findings(text)))

    def test_rejects_private_filesystem_path(self) -> None:
        text = "Read " + "/".join(("", "home", "operator", "settings.json"))
        self.assertTrue(any("private filesystem path" in item for item in self.findings(text)))

    def test_rejects_chat_identifier(self) -> None:
        text = "chat" + "_id: 123456789"
        self.assertTrue(any("chat identifier" in item for item in self.findings(text)))

    def test_rejects_private_hostname(self) -> None:
        text = "builder" + ".internal"
        self.assertTrue(any("private hostname" in item for item in self.findings(text)))

    def test_rejects_secret_shaped_assignment(self) -> None:
        text = "api" + "_key=" + "a" * 24
        self.assertTrue(any("sanitization pattern" in item for item in self.findings(text)))


if __name__ == "__main__":
    unittest.main()
