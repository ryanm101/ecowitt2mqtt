"""Helpers for config validation using voluptuous."""
from __future__ import annotations

from collections.abc import Callable
from numbers import Number
from typing import Any

import voluptuous as vol


def has_at_least_one_key(*keys: Any) -> Callable[[dict], dict]:
    """Validate that at least one key exists.

    Adapted from:
    https://github.com/alecthomas/voluptuous/issues/115#issuecomment-144464666
    """

    def validate(obj: dict) -> dict:
        """Test keys exist in dict."""
        if not isinstance(obj, dict):
            raise vol.Invalid("Invalid object (expected a dictionary)")

        for k in obj:
            if k in keys:
                return obj
        expected = ", ".join(str(k) for k in keys)
        raise vol.Invalid(f"Must contain at least one of: {expected}")

    return validate


def boolean(value: Any) -> bool:
    """Validate and coerce a boolean value."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.lower().strip()
        if value in ("1", "true", "yes", "on", "enable"):
            return True
        if value in ("0", "false", "no", "off", "disable"):
            return False
    elif isinstance(value, Number):
        # type ignore: https://github.com/python/mypy/issues/3186
        return value != 0  # type: ignore[comparison-overlap]
    raise vol.Invalid(f"Invalid boolean value: {value}")


port = vol.All(vol.Coerce(int), vol.Range(min=1, max=65535))


def string(value: Any) -> str:
    """Validate and coerce a value to string, except for None."""
    if value is None:
        raise vol.Invalid("Invalid string value: None")
    if isinstance(value, (list, dict)):
        raise vol.Invalid(f"Invalid string value: {value}")
    return str(value)
