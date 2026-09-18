"""Проверка опубликованных версий приложения на GitHub."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GITHUB_OWNER = "Sugo174"
GITHUB_REPOSITORY = "Smart-electric-meter-configurator"

LATEST_RELEASE_API_URL = (
    "https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPOSITORY}/releases/latest"
)


def normalize_version(version):
    """Приводит Git-тег v1.10 или v.1.10 к формату 1.10."""
    normalized_version = str(version).strip()

    if normalized_version.lower().startswith("v"):
        normalized_version = normalized_version[1:]

    return normalized_version.lstrip(".")


def version_to_tuple(version):
    """Преобразует версию вида 1.10 в кортеж чисел для сравнения."""
    normalized_version = normalize_version(version)

    try:
        return tuple(
            int(part)
            for part in normalized_version.split(".")
        )
    except ValueError as error:
        raise ValueError(
            f"Unsupported version format: {version}"
        ) from error


def is_version_newer(latest_version, current_version):
    """Проверяет, новее ли опубликованная версия установленной."""
    latest_parts = version_to_tuple(latest_version)
    current_parts = version_to_tuple(current_version)

    length = max(
        len(latest_parts),
        len(current_parts),
    )

    latest_parts += (0,) * (length - len(latest_parts))
    current_parts += (0,) * (length - len(current_parts))

    return latest_parts > current_parts


def get_latest_release(timeout=5):
    """Возвращает последнюю опубликованную версию GitHub Release.

    Возвращает:
        (True, {"version": str, "release_url": str})
        или
        (False, код_ошибки).
    """
    request = Request(
        LATEST_RELEASE_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Smart-Meter-Configurator",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            release_data = json.load(response)

        return True, {
            "version": normalize_version(
                release_data["tag_name"]
            ),
            "release_url": release_data["html_url"],
        }

    except (HTTPError, URLError, TimeoutError):
        return False, "network_error"

    except (
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ):
        return False, "invalid_release_data"