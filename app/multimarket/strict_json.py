"""Shared strict JSON primitives for public multimarket payloads."""

from __future__ import annotations

from typing import Any


class DuplicateJsonKey(ValueError):
    """Raised when a JSON object repeats one of its keys."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build an object while rejecting duplicate keys at every nesting level."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKey
        result[key] = value
    return result
