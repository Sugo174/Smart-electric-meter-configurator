"""Тесты проверки версий и данных GitHub Release."""

import io
import unittest
from unittest.mock import patch
from urllib.error import URLError

from update_checker import (
    get_latest_release,
    is_version_newer,
    normalize_version,
)


class VersionComparisonTests(unittest.TestCase):
    """Проверяет обработку и сравнение номеров версий."""

    def test_normalizes_release_tags(self):
        """Удаляет варианты префикса v из Git-тегов."""
        self.assertEqual(
            normalize_version("v1.10"),
            "1.10",
        )
        self.assertEqual(
            normalize_version("v.1.09"),
            "1.09",
        )

    def test_detects_newer_version(self):
        """Определяет, что 1.10 новее 1.09."""
        self.assertTrue(
            is_version_newer("1.10", "1.09")
        )

    def test_handles_equal_version_lengths(self):
        """Считает 1.10 и 1.10.0 одной версией."""
        self.assertFalse(
            is_version_newer("1.10.0", "1.10")
        )


class LatestReleaseTests(unittest.TestCase):
    """Проверяет чтение ответа GitHub без реального запроса в сеть."""

    def test_reads_latest_release_data(self):
        """Получает версию и ссылку из ответа GitHub API."""
        response = io.StringIO(
            '{"tag_name": "v1.10", '
            '"html_url": "https://example.com/release"}'
        )

        with patch(
            "update_checker.urlopen",
            return_value=response,
        ):
            success, result = get_latest_release()

        self.assertTrue(success)
        self.assertEqual(
            result["version"],
            "1.10",
        )
        self.assertEqual(
            result["release_url"],
            "https://example.com/release",
        )

    def test_returns_network_error(self):
        """Возвращает понятный код при ошибке сети."""
        with patch(
            "update_checker.urlopen",
            side_effect=URLError("No connection"),
        ):
            success, result = get_latest_release()

        self.assertFalse(success)
        self.assertEqual(result, "network_error")


if __name__ == "__main__":
    unittest.main()