"""Support for the Miele Binary Sensors."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MieleDataUpdateCoordinator
from .entity import MieleEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Load Sensors from the config settings."""
    coordinator: MieleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[MieleEntity] = []
    devices = coordinator.data
    for _, device in devices.items():
        entities.append(MieleDevice(coordinator, device))

    async_add_entities(entities, True)
    coordinator.remove_old_entities(DOMAIN)


class MieleDevice(MieleEntity):
    """Miele Device, is actually status sensor, Migrated from Older verison."""

    def __init__(
        self,
        coordinator: MieleDataUpdateCoordinator,
        device: dict[str, any],
    ):
        """Initialise Miele Device Entity."""
        super().__init__(coordinator, DOMAIN, device)

    @property
    def state(self):
        """Return the state of the sensor."""
        result = self.device["state"]["status"]["value_localized"]
        if result is None:
            result = self.device["state"]["status"]["value_raw"]

        return result

    @property
    def extra_state_attributes(self):
        """Attributes."""

        result = {}
        result["state_raw"] = self.device["state"]["status"]["value_raw"]

        result["model"] = self.device["ident"]["deviceIdentLabel"]["techType"]
        result["device_type"] = self.device["ident"]["type"]["value_localized"]
        result["fabrication_number"] = self.device["ident"]["deviceIdentLabel"][
            "fabNumber"
        ]

        result["gateway_type"] = self.device["ident"]["xkmIdentLabel"]["techType"]
        result["gateway_version"] = self.device["ident"]["xkmIdentLabel"][
            "releaseVersion"
        ]

        return result

    async def action(self, action):
        """Peform Action on Device."""
        await self.coordinator.client.action(self.unique_id, action)

    async def start_program(self, program_id):
        """Start Program on Device."""
        await self.coordinator.client.start_program(self.unique_id, program_id)
