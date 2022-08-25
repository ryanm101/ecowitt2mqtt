"""Define MQTT publishing."""
from __future__ import annotations

from ecowitt2mqtt.const import LOGGER
from ecowitt2mqtt.data import ProcessedData
from ecowitt2mqtt.helpers.publisher import MqttPublisher, generate_mqtt_payload
from ecowitt2mqtt.helpers.typing import DataValueType


class TopicPublisher(MqttPublisher):
    """Define an MQTT publisher that publishes to a topic."""

    async def async_publish(self, data: dict[str, DataValueType]) -> None:
        """Publish to MQTT."""
        if not self.config.raw_data:
            processed_data = ProcessedData(self.config, data)
            data = {key: value.value for key, value in processed_data.output.items()}

        await self.client.publish(
            self.config.mqtt_topic,
            payload=generate_mqtt_payload(data),
            retain=self.config.mqtt_retain,
        )

        LOGGER.info("Published to %s", self.config.mqtt_topic)
        LOGGER.debug("Published data: %s", data)
