"""Support for the Miele Fan Entities."""

import logging
import math

from typing import Optional

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    int_states_in_range,
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .const import DOMAIN
from .coordinator import MieleDataUpdateCoordinator
from .entity import MieleEntity

_LOGGER = logging.getLogger(__name__)

SUPPORTED_TYPES = [18]
SPEED_RANGE = (1, 4)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Load Sensors from the config settings."""
    coordinator: MieleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[FanEntity] = []
    devices = coordinator.data
    for _, device in devices.items():
        device_type = device["ident"]["type"]["value_raw"]

        if device_type in SUPPORTED_TYPES:
            entities.append(MieleFan(coordinator, device))

    async_add_entities(entities, True)
    coordinator.remove_old_entities(Platform.SENSOR)


class MieleFan(MieleEntity, FanEntity):
    """Miele Fan Entity."""

    def __init__(self, coordinator: MieleDataUpdateCoordinator, device: dict[str, any]):
        """Initialize Entity."""
        super().__init__(coordinator, "fan", device, "fan")
        self._current_speed = 0

    @property
    def is_on(self):
        """Return the state of the fan."""
        value_raw = self.device["state"]["ventilationStep"]["value_raw"]
        return value_raw is not None and value_raw != 0

    @property
    def supported_features(self):
        """Flag supported features."""
        return FanEntityFeature.SET_SPEED

    @property
    def speed(self):
        """Return the current speed."""
        return self.device["state"]["ventilationStep"]["value_raw"]

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        return ranged_value_to_percentage(SPEED_RANGE, self._current_speed)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return int_states_in_range(SPEED_RANGE)

    def turn_on(
        self, percentage: int | None = None, preset_mode: str | None = None, **kwargs
    ) -> None:
        """Turn on the fan."""
        if percentage == "0":
            self.turn_off()

        client = self.coordinator.client
        client.action(device_id=self.device_id, body={"powerOn": True})

    async def async_turn_on(
        self, percentage: int | None = None, preset_mode: str | None = None, **kwargs
    ):
        """Turn on the fan."""
        if percentage == "0":
            await self.async_turn_off()

        elif percentage:
            await self.async_set_percentage(percentage=percentage)
            client = self.coordinator.client
            await client.action(device_id=self.device_id, body={"powerOn": True})
        else:
            _LOGGER.debug("Turning on")
            client = self.coordinator.client
            await client.action(device_id=self.device_id, body={"powerOn": True})

    def turn_off(self, **kwargs):
        """Turn off the Fan."""
        _LOGGER.debug("Turning off")
        client = self.coordinator.client
        client.action(device_id=self.device_id, body={"powerOff": True})

    async def async_turn_off(self, **kwargs):
        """Turn Off the Fan Async."""
        client = self.coordinator.client
        await client.action(device_id=self.device_id, body={"powerOff": True})

    def set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""  # TODO:
        value_in_range = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        self._current_speed = value_in_range
        _LOGGER.debug(f"Setting speed to : {value_in_range}")
        client = self.coordinator.client
        client.action(
            device_id=self.device_id, body={"ventilationStep": value_in_range}
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""  #
        value_in_range = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        self._current_speed = value_in_range
        _LOGGER.debug(f"Setting speed to : {value_in_range}")
        client = self.coordinator.client
        await client.action(
            device_id=self.device_id, body={"ventilationStep": value_in_range}
        )
