"""Helpers for config validation using voluptuous."""
from __future__ import annotations

from numbers import Number
from typing import Any

import voluptuous as vol

from ecowitt2mqtt.helpers.calculator.battery import BatteryStrategy


def battery_override(
    value: str | tuple[str, str] | dict[str, Any]
) -> dict[str, BatteryStrategy]:
    """Validate and coerce one or more battery overrides."""
    try:
        if isinstance(value, dict):
            return {key: BatteryStrategy(val) for key, val in value.items()}

        if isinstance(value, tuple):
            return {
                pair[0]: BatteryStrategy(pair[1])
                for assignment in value
                if (pair := assignment.split("="))
            }

        return {
            pair[0]: BatteryStrategy(pair[1])
            for assignment in value.split(";")
            if (pair := assignment.split("="))
        }
    except IndexError as err:
        raise vol.Invalid(f"invalid battery override definition: {value}") from err
    except ValueError as err:
        raise vol.Invalid(f"invalid battery override value: {value}") from err


def battery_strategy(value: str) -> BatteryStrategy:
    """Validate and coerce a battery strategy."""
    try:
        return BatteryStrategy(value)
    except ValueError as err:
        raise vol.Invalid(f"invalid strategy: {value}") from err


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
    raise vol.Invalid(f"invalid boolean value: {value}")


port = vol.All(vol.Coerce(int), vol.Range(min=1, max=65535))


def string(value: Any) -> str | None:
    """Validate and coerce a value to string, except for None."""
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        raise vol.Invalid(f"invalid string value: {value}")
    return str(value)
