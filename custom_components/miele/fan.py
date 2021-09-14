import logging
import math
from datetime import timedelta
from typing import Optional

from homeassistant.components.fan import SUPPORT_SET_SPEED, FanEntity
from homeassistant.helpers.entity import Entity
from homeassistant.util.percentage import (
    int_states_in_range,
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from custom_components.miele import DATA_CLIENT, DATA_DEVICES
from custom_components.miele import DOMAIN as MIELE_DOMAIN

PLATFORMS = ["miele"]

_LOGGER = logging.getLogger(__name__)

ALL_DEVICES = []

SUPPORTED_TYPES = [18]


SPEED_RANGE = (1, 4)


# pylint: disable=W0612
def setup_platform(hass, config, add_devices, discovery_info=None):
    global ALL_DEVICES

    devices = hass.data[MIELE_DOMAIN][DATA_DEVICES]
    for k, device in devices.items():
        device_type = device["ident"]["type"]

        fan_devices = []
        if device_type["value_raw"] in SUPPORTED_TYPES:
            fan_devices.append(MieleFan(hass, device))

        add_devices(fan_devices)
        ALL_DEVICES = ALL_DEVICES + fan_devices


def update_device_state():
    for device in ALL_DEVICES:
        try:
            device.async_schedule_update_ha_state(True)
        except (AssertionError, AttributeError):
            _LOGGER.debug(
                "Component most likely is disabled manually, if not please report to developer"
                "{}".format(device.entity_id)
            )


class MieleFan(FanEntity):
    def __init__(self, hass, device):
        self._hass = hass
        self._device = device
        self._ha_key = "fan"
        self._current_speed = 0

    @property
    def device_id(self):
        """Return the unique ID for this fan."""
        return self._device["ident"]["deviceIdentLabel"]["fabNumber"]

    @property
    def unique_id(self):
        """Return the unique ID for this fan."""
        return self.device_id

    @property
    def name(self):
        """Return the name of the fan."""
        ident = self._device["ident"]

        result = ident["deviceName"]
        if len(result) == 0:
            return ident["type"]["value_localized"]
        else:
            return result

    @property
    def is_on(self):
        """Return the state of the fan."""
        return self._device["state"]["ventilationStep"]["value_raw"] != 0

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def speed(self):
        """Return the current speed"""
        return self._device["state"]["ventilationStep"]["value_raw"]

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        return ranged_value_to_percentage(SPEED_RANGE, self._current_speed)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return int_states_in_range(SPEED_RANGE)

    def turn_on(self, percentage: Optional[int] = None, **kwargs) -> None:
        """Turn on the fan."""
        value_in_range = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        if percentage == "0":
            self.turn_off()
        client = self._hass.data[MIELE_DOMAIN][DATA_CLIENT]
        client.action(device_id=self.device_id, body={"powerOn": True})

    async def async_turn_on(self, percentage: Optional[int] = None, **kwargs):
        """Turn on the fan."""
        if percentage == "0":
            await self.async_turn_off()
        elif percentage is not None:
            await self.async_set_percentage(percentage=percentage)
            client = self._hass.data[MIELE_DOMAIN][DATA_CLIENT]
            await client.action(device_id=self.device_id, body={"powerOn": True})
        else:
            _LOGGER.debug("Turning on")
            client = self._hass.data[MIELE_DOMAIN][DATA_CLIENT]
            await client.action(device_id=self.device_id, body={"powerOn": True})

    def turn_off(self, **kwargs):
        _LOGGER.debug("Turning off")
        client = self._hass.data[MIELE_DOMAIN][DATA_CLIENT]
        client.action(device_id=self.device_id, body={"powerOff": True})

    async def async_turn_off(self, **kwargs):
        client = self._hass.data[MIELE_DOMAIN][DATA_CLIENT]
        await client.action(device_id=self.device_id, body={"powerOff": True})

    def set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""  # TODO:
        value_in_range = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        self._current_speed = value_in_range
        _LOGGER.debug("Setting speed to : {}".format(value_in_range))
        client = self._hass.data[MIELE_DOMAIN][DATA_CLIENT]
        client.action(
            device_id=self.device_id, body={"ventilationStep": value_in_range}
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""  #
        value_in_range = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        self._current_speed = value_in_range
        _LOGGER.debug("Setting speed to : {}".format(value_in_range))
        client = self._hass.data[MIELE_DOMAIN][DATA_CLIENT]
        await client.action(
            device_id=self.device_id, body={"ventilationStep": value_in_range}
        )

    async def async_update(self):
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.debug("Miele device not found: {}".format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]
