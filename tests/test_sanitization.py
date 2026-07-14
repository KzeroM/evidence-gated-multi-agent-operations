"""Positive and negative tests for configurable public-safety scanning."""

from __future__ import annotations

import unittest

from egmo.protocol import sanitization_findings


class SanitizationTests(unittest.TestCase):
    def findings(self, text: str) -> list[str]:
        return sanitization_findings("fixture.txt", text)

    def test_allows_fictional_public_values(self) -> None:
        text = "reviewer" + "@" + "example.org 192.0.2.20 [2001:db8::20] token=<redacted>"
        self.assertEqual(self.findings(text), [])

    def test_rejects_non_example_email(self) -> None:
        text = "operator" + "@" + "corp" + ".invalid"
        self.assertTrue(any("non-example email" in item for item in self.findings(text)))

    def test_rejects_ipv4(self) -> None:
        text = ".".join(("8", "8", "4", "4"))
        self.assertTrue(any("IPv4" in item for item in self.findings(text)))

    def test_rejects_ipv6(self) -> None:
        text = ":".join(("2606", "4700", "4700", "", "1111"))
        self.assertTrue(any("IPv6" in item for item in self.findings(text)))

    def test_rejects_posix_path(self) -> None:
        text = "/".join(("", "home", "sample-user", "private.txt"))
        self.assertTrue(any("POSIX" in item for item in self.findings(text)))

    def test_rejects_windows_path(self) -> None:
        text = "C:" + "\\" + "Users" + "\\" + "sample-user" + "\\" + "private.txt"
        self.assertTrue(any("Windows" in item for item in self.findings(text)))

    def test_rejects_environment_shaped_secret(self) -> None:
        text = "PASS" + "WORD=" + "fictional-but-secret-shaped"
        self.assertTrue(any("secret-shaped" in item for item in self.findings(text)))

    def test_rejects_private_hostname_and_chat_id(self) -> None:
        text = "build" + "er.internal room" + "_id=ABCDEF1234"
        findings = self.findings(text)
        self.assertTrue(any("hostname" in item for item in findings))
        self.assertTrue(any("chat identifier" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
