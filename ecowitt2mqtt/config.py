"""Define a configuration management module."""
from __future__ import annotations

import os
from typing import Any, Dict, cast

from ruamel.yaml import YAML
import voluptuous as vol

from ecowitt2mqtt.const import (
    CONF_BATTERY_OVERRIDES,
    CONF_CONFIG,
    CONF_DEFAULT_BATTERY_STRATEGY,
    CONF_DIAGNOSTICS,
    CONF_DISABLE_CALCULATED_DATA,
    CONF_ENDPOINT,
    CONF_HASS_DISCOVERY,
    CONF_HASS_DISCOVERY_PREFIX,
    CONF_HASS_ENTITY_ID_PREFIX,
    CONF_INPUT_UNIT_SYSTEM,
    CONF_MQTT_BROKER,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_PORT,
    CONF_MQTT_RETAIN,
    CONF_MQTT_TLS,
    CONF_MQTT_TOPIC,
    CONF_MQTT_USERNAME,
    CONF_OUTPUT_UNIT_SYSTEM,
    CONF_PORT,
    CONF_RAW_DATA,
    CONF_VERBOSE,
    DEFAULT_ENDPOINT,
    DEFAULT_HASS_DISCOVERY_PREFIX,
    DEFAULT_MQTT_PORT,
    DEFAULT_PORT,
    ENV_BATTERY_OVERRIDE,
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
    UNIT_SYSTEMS,
    UNIT_SYSTEM_IMPERIAL,
)
from ecowitt2mqtt.errors import EcowittError
from ecowitt2mqtt.helpers.calculator.battery import BatteryStrategy
import ecowitt2mqtt.helpers.config_validation as cv
from ecowitt2mqtt.helpers.typing import UnitSystemType

CONF_DEFAULT = "default"
CONF_GATEWAYS = "gateways"

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

CONFIG_SCHEMA = vol.All(
    cv.has_at_least_one_key(CONF_HASS_DISCOVERY, CONF_MQTT_TOPIC),
    vol.Schema(
        {
            vol.Required(CONF_MQTT_BROKER): cv.string,
            vol.Exclusive(CONF_HASS_DISCOVERY, "publisher", default=False): cv.boolean,
            vol.Exclusive(CONF_MQTT_TOPIC, "publisher"): cv.string,
            vol.Optional(
                CONF_DEFAULT_BATTERY_STRATEGY, default=BatteryStrategy.BOOLEAN
            ): vol.All(cv.string, vol.In(BatteryStrategy)),
            vol.Optional(CONF_DIAGNOSTICS, default=False): cv.boolean,
            vol.Optional(CONF_DISABLE_CALCULATED_DATA, default=False): cv.boolean,
            vol.Optional(CONF_ENDPOINT, default=DEFAULT_ENDPOINT): cv.string,
            vol.Optional(
                CONF_HASS_ENTITY_ID_PREFIX, default=DEFAULT_HASS_DISCOVERY_PREFIX
            ): cv.string,
            vol.Optional(CONF_INPUT_UNIT_SYSTEM, default=UNIT_SYSTEM_IMPERIAL): vol.All(
                cv.string, vol.In(UNIT_SYSTEMS)
            ),
            vol.Optional(CONF_MQTT_PASSWORD): cv.string,
            vol.Optional(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): cv.port,
            vol.Optional(CONF_MQTT_RETAIN, default=False): cv.boolean,
            vol.Optional(CONF_MQTT_TLS, default=False): cv.boolean,
            vol.Optional(CONF_MQTT_USERNAME, default=False): cv.boolean,
            vol.Optional(
                CONF_OUTPUT_UNIT_SYSTEM, default=UNIT_SYSTEM_IMPERIAL
            ): vol.All(cv.string, vol.In(UNIT_SYSTEMS)),
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
            vol.Optional(CONF_RAW_DATA, default=False): cv.boolean,
            vol.Optional(CONF_VERBOSE, default=False): cv.boolean,
        }
    ),
)


class ConfigError(EcowittError):
    """Define an error related to bad configuration."""

    pass


def convert_battery_config(configs: str | tuple) -> dict[str, BatteryStrategy]:
    """Normalize incoming battery configurations depending on the input format.

    1. Environment Variables (str): "key1=value1;key2=value2"
    2. CLI Options (tuple): ("key1=val1", "key2=val2")
    """
    try:
        if isinstance(configs, str):
            return {
                pair[0]: BatteryStrategy(pair[1])
                for assignment in configs.split(";")
                if (pair := assignment.split("="))
            }
        return {
            pair[0]: BatteryStrategy(pair[1])
            for assignment in configs
            if (pair := assignment.split("="))
        }
    except (IndexError, KeyError, ValueError) as err:
        raise ConfigError(f"Unable to parse battery configurations: {configs}") from err


class Config:
    """Define the configuration management object."""

    def __init__(self, config_id: str, config: dict[str, Any]) -> None:
        """Initialize."""
        LOGGER.debug("Initializing config ID %s with data: %s", config_id, config)

        # if CONF_MQTT_BROKER not in config:
        #     raise ConfigError(
        #         f"Missing required configuration option: {CONF_MQTT_BROKER}"
        #     )

        # if not any(
        #     data.get(key)
        #     for key in (CONF_MQTT_TOPIC, CONF_HASS_DISCOVERY)
        #     for data in (self._config, params)
        # ):
        #     raise ConfigError(
        #         "Missing required option: --mqtt-topic or --hass-discovery"
        #     )

        self._config = {CONF_BATTERY_OVERRIDES: {}}

        # Merge the CLI options/environment variables; if the value is falsey (but *not*
        # False), ignore it:
        for key, value in config.items():
            if key == CONF_DEFAULT_BATTERY_STRATEGY:
                self._config[key] = BatteryStrategy(value)
            if value is not None:
                self._config[key] = value

        if env_battery_overrides := os.getenv(ENV_BATTERY_OVERRIDE):
            self._config[CONF_BATTERY_OVERRIDES] = convert_battery_config(
                env_battery_overrides
            )
        elif CONF_BATTERY_OVERRIDES in params:
            self._config[CONF_BATTERY_OVERRIDES] = convert_battery_config(
                params[CONF_BATTERY_OVERRIDES]
            )

        LOGGER.debug("Loaded Config: %s", self._config)

    @property
    def battery_overrides(self) -> dict[str, BatteryStrategy]:
        """Return the battery overrides."""
        return cast(
            Dict[str, BatteryStrategy], self._config.get(CONF_BATTERY_OVERRIDES)
        )

    @property
    def default_battery_strategy(self) -> BatteryStrategy:
        """Return the default battery strategy."""
        return cast(BatteryStrategy, self._config.get(CONF_DEFAULT_BATTERY_STRATEGY))

    @property
    def diagnostics(self) -> bool:
        """Return whether diagnostics is enabled."""
        return cast(bool, self._config.get(CONF_DIAGNOSTICS, False))

    @property
    def disable_calculated_data(self) -> bool:
        """Return whether calculated sensor output is disabled."""
        return cast(bool, self._config.get(CONF_DISABLE_CALCULATED_DATA, False))

    @property
    def endpoint(self) -> str:
        """Return the ecowitt2mqtt API endpoint."""
        return cast(str, self._config.get(CONF_ENDPOINT))

    @property
    def hass_discovery(self) -> bool:
        """Return whether Home Assistant Discovery should be used."""
        return cast(bool, self._config.get(CONF_HASS_DISCOVERY, False))

    @property
    def hass_discovery_prefix(self) -> str:
        """Return the Home Assistant Discovery MQTT prefix."""
        return cast(str, self._config.get(CONF_HASS_DISCOVERY_PREFIX))

    @property
    def hass_entity_id_prefix(self) -> str | None:
        """Return the Home Assistant entity ID prefix."""
        return self._config.get(CONF_HASS_ENTITY_ID_PREFIX)

    @property
    def input_unit_system(self) -> UnitSystemType:
        """Return the input unit system."""
        return cast(UnitSystemType, self._config.get(CONF_INPUT_UNIT_SYSTEM))

    @property
    def mqtt_broker(self) -> str:
        """Return the MQTT broker host/IP address."""
        return cast(str, self._config.get(CONF_MQTT_BROKER))

    @property
    def mqtt_password(self) -> str:
        """Return the MQTT broker password."""
        return cast(str, self._config.get(CONF_MQTT_PASSWORD))

    @property
    def mqtt_port(self) -> int:
        """Return the MQTT broker port."""
        return cast(int, self._config.get(CONF_MQTT_PORT))

    @property
    def mqtt_retain(self) -> bool:
        """Return whether MQTT messages should be retained."""
        return cast(bool, self._config.get(CONF_MQTT_RETAIN, False))

    @property
    def mqtt_tls(self) -> bool:
        """Return whether MQTT over TLS is configured."""
        return cast(bool, self._config.get(CONF_MQTT_TLS, False))

    @property
    def mqtt_topic(self) -> str | None:
        """Return the MQTT broker topic."""
        return self._config.get(CONF_MQTT_TOPIC)

    @property
    def mqtt_username(self) -> str:
        """Return the MQTT broker username."""
        return cast(str, self._config.get(CONF_MQTT_USERNAME))

    @property
    def output_unit_system(self) -> UnitSystemType:
        """Return the output unit system."""
        return cast(UnitSystemType, self._config.get(CONF_OUTPUT_UNIT_SYSTEM))

    @property
    def port(self) -> int:
        """Return the ecowitt2mqtt API port."""
        return cast(int, self._config.get(CONF_PORT))

    @property
    def raw_data(self) -> bool:
        """Return whether raw data is configured."""
        return cast(bool, self._config.get(CONF_RAW_DATA, False))

    @property
    def verbose(self) -> bool:
        """Return whether verbose logging is enabled."""
        return cast(bool, self._config.get(CONF_VERBOSE, False))


class ConfigFileManager:
    """Define a manager of data loaded from a config file."""

    def __init__(self) -> None:
        """Initialize."""
        self._cli_options_env_vars: dict[str, Any] = {}
        self._config_file_data: dict[str, Any] = {}
        self._configs: dict[str, Config] = {}

    @property
    def configs(self) -> dict[str, Config]:
        """Return all parsed Config objects."""
        return self._configs

    def load_cli_options_env_vars(self, cli_options_env_vars: dict[str, Any]) -> None:
        """Load config data from CLI options/env vars."""
        self._cli_options_env_vars = cli_options_env_vars

    def load_config_file(self, config_path: str) -> None:
        """Load config data from a YAML or JSON file."""
        for legacy_env_var, new_env_var in DEPRECATED_ENV_VAR_MAP.items():
            if os.getenv(legacy_env_var) is None:
                continue
            LOGGER.warning(
                "Environment variable %s is deprecated; use %s instead",
                legacy_env_var,
                new_env_var,
            )

        parser = YAML(typ="safe")
        with open(config_path, encoding="utf-8") as config_file:
            self._config_file_data = parser.load(config_file)

        if not isinstance(self._config_file_data, dict):
            raise ConfigError(f"Unable to parse config file: {config_path}")

        # default_config = file_config_data.get(CONF_DEFAULT, {})
        # LOGGER.debug("Default config from config file: %s", default_config)
        # gateways_config = file_config_data.get(CONF_GATEWAYS, {})
        # LOGGER.debug("Gateway configs from config file: %s", gateways_config)

        # for passkey, gateway_config in gateways_config.items():
        #     merged_config = {**default_config, **gateway_config}
