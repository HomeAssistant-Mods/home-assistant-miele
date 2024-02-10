"""Support for the Miele Binary Sensors."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CAPABILITIES
from .coordinator import MieleDataUpdateCoordinator
from .entity import MieleEntity

_LOGGER = logging.getLogger(__name__)


def _map_key(key):
    if key == "signalInfo":
        return "Info"
    elif key == "signalFailure":
        return "Failure"
    elif key == "signalDoor":
        return "Door"
    elif key == "mobileStart":
        return "Mobile Start"


def state_capability(type, state) -> bool:
    """Check the capabilities."""
    type_str = str(type)
    if state in CAPABILITIES[type_str]:
        return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Load Sensors from the config settings."""
    coordinator: MieleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []
    devices = coordinator.data
    for _, device in devices.items():
        device_state = device["state"]
        device_type = device["ident"]["type"]["value_raw"]

        if "signalInfo" in device_state and state_capability(
            type=device_type, state="signalInfo"
        ):
            entities.append(MieleBinarySensor(coordinator, device, "signalInfo"))
        if "signalFailure" in device_state and state_capability(
            type=device_type, state="signalFailure"
        ):
            entities.append(MieleBinarySensor(coordinator, device, "signalFailure"))
        if "signalDoor" in device_state and state_capability(
            type=device_type, state="signalDoor"
        ):
            entities.append(MieleBinarySensor(coordinator, device, "signalDoor"))
        if "remoteEnable" in device_state and state_capability(
            type=device_type, state="remoteEnable"
        ):
            remote_state = device_state["remoteEnable"]
            if "mobileStart" in remote_state:
                entities.append(
                    MieleBinarySensor(coordinator, device, "remoteEnable.mobileStart")
                )

    async_add_entities(entities, True)


class MieleBinarySensor(MieleEntity, BinarySensorEntity):
    """Binary Sensor Entity."""

    def __init__(
        self,
        coordinator: MieleDataUpdateCoordinator,
        device: dict[str, any],
        dot_key: str,
    ):
        """Initialize Entity."""
        self._keys = dot_key.split(".")
        super().__init__(
            coordinator,
            device,
            self._keys[-1],
            _map_key(self._keys[-1]),
        )

    @property
    def is_on(self):
        """Return the state of the sensor."""
        current_val = self._device["state"]
        for k in self._keys:
            current_val = current_val[k]
        return bool(current_val)

    @property
    def device_class(self):
        """Return the Device Class."""
        if self._key == "signalDoor":
            return "door"
        elif self._key == "mobileStart":
            return "running"
        else:
            return "problem"
