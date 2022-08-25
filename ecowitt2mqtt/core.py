"""Define the core application objects."""
from __future__ import annotations

import logging
import os
from typing import Any

from ecowitt2mqtt.config import Config, Configs
from ecowitt2mqtt.const import (
    CONF_VERBOSE,
    ENV_ENDPOINT,
    ENV_HASS_DISCOVERY,
    ENV_HASS_DISCOVERY_PREFIX,
    ENV_HASS_ENTITY_ID_PREFIX,
    ENV_INPUT_UNIT_SYSTEM,
    ENV_MQTT_BROKER,
    ENV_MQTT_PASSWORD,
    ENV_MQTT_PORT,
    ENV_MQTT_TOPIC,
    ENV_MQTT_USERNAME,
    ENV_OUTPUT_UNIT_SYSTEM,
    ENV_PORT,
    ENV_RAW_DATA,
    ENV_VERBOSE,
    LEGACY_ENV_ENDPOINT,
    LEGACY_ENV_HASS_DISCOVERY,
    LEGACY_ENV_HASS_DISCOVERY_PREFIX,
    LEGACY_ENV_HASS_ENTITY_ID_PREFIX,
    LEGACY_ENV_INPUT_UNIT_SYSTEM,
    LEGACY_ENV_LOG_LEVEL,
    LEGACY_ENV_MQTT_BROKER,
    LEGACY_ENV_MQTT_PASSWORD,
    LEGACY_ENV_MQTT_PORT,
    LEGACY_ENV_MQTT_TOPIC,
    LEGACY_ENV_MQTT_USERNAME,
    LEGACY_ENV_OUTPUT_UNIT_SYSTEM,
    LEGACY_ENV_PORT,
    LEGACY_ENV_RAW_DATA,
    LOGGER,
    __version__ as ecowitt2mqtt_version,
)
from ecowitt2mqtt.helpers.logging import TyperLoggerHandler
from ecowitt2mqtt.runtime import Runtime

DEPRECATED_ENV_VAR_MAP = {
    LEGACY_ENV_ENDPOINT: ENV_ENDPOINT,
    LEGACY_ENV_HASS_DISCOVERY: ENV_HASS_DISCOVERY,
    LEGACY_ENV_HASS_DISCOVERY_PREFIX: ENV_HASS_DISCOVERY_PREFIX,
    LEGACY_ENV_HASS_ENTITY_ID_PREFIX: ENV_HASS_ENTITY_ID_PREFIX,
    LEGACY_ENV_INPUT_UNIT_SYSTEM: ENV_INPUT_UNIT_SYSTEM,
    LEGACY_ENV_LOG_LEVEL: ENV_VERBOSE,
    LEGACY_ENV_MQTT_BROKER: ENV_MQTT_BROKER,
    LEGACY_ENV_MQTT_PASSWORD: ENV_MQTT_PASSWORD,
    LEGACY_ENV_MQTT_PORT: ENV_MQTT_PORT,
    LEGACY_ENV_MQTT_TOPIC: ENV_MQTT_TOPIC,
    LEGACY_ENV_MQTT_USERNAME: ENV_MQTT_USERNAME,
    LEGACY_ENV_OUTPUT_UNIT_SYSTEM: ENV_OUTPUT_UNIT_SYSTEM,
    LEGACY_ENV_PORT: ENV_PORT,
    LEGACY_ENV_RAW_DATA: ENV_RAW_DATA,
}


class Ecowitt:  # pylint: disable=too-few-public-methods
    """Define the base application object."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize."""
        if config.get(CONF_VERBOSE) or os.getenv(LEGACY_ENV_LOG_LEVEL):
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            handlers=(TyperLoggerHandler(),),
        )

        for legacy_env_var, new_env_var in DEPRECATED_ENV_VAR_MAP.items():
            if os.getenv(legacy_env_var) is None:
                continue
            LOGGER.warning(
                "Environment variable %s is deprecated; use %s instead",
                legacy_env_var,
                new_env_var,
            )

        self.configs = Configs(config)
        self.runtime = Runtime(self)

    async def async_start(self) -> None:
        """Start ecowitt2mqtt."""
        LOGGER.info("Starting ecowitt2mqtt (version %s)", ecowitt2mqtt_version)
        await self.runtime.async_start()
