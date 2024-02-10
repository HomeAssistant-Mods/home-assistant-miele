"""Support for the Miele Light Sensors."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MieleDataUpdateCoordinator
from .entity import MieleEntity

_LOGGER = logging.getLogger(__name__)

SUPPORTED_TYPES = [17, 18, 32, 33, 34, 68]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Load Sensors from the config settings."""
    coordinator: MieleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[LightEntity] = []
    devices = coordinator.data
    for _, device in devices.items():
        device_type = device["ident"]["type"]["value_raw"]

        if device_type in SUPPORTED_TYPES:
            entities.append(MieleLight(coordinator, device))

    async_add_entities(entities, True)


class MieleLight(MieleEntity, LightEntity):
    """Miele Light Entity."""

    def __init__(self, coordinator: MieleDataUpdateCoordinator, device: dict[str, any]):
        """Initialize Light Entity."""
        super().__init__(coordinator, device, "light")
        self._hass = coordinator.hass

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return self._device["state"]["light"] == 1

    def turn_on(self, **kwargs):
        """Call Service to turn on the Light."""
        service_parameters = {"device_id": self.device_id, "body": {"light": 1}}
        self._hass.services.call(DOMAIN, "action", service_parameters)

    def turn_off(self, **kwargs):
        """Call Service to turn off the Light."""
        service_parameters = {"device_id": self.device_id, "body": {"light": 2}}
        self._hass.services.call(DOMAIN, "action", service_parameters)
