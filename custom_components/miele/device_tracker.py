"""Support for the Miele Device Tracker Entities.

This uses a tracker for the Device to handle services and support
Migration from the original Platform based approach.
"""

import logging
import voluptuous as vol

from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import DOMAIN
from .coordinator import MieleDataUpdateCoordinator
from .entity import MieleEntity

_LOGGER = logging.getLogger(__name__)

SERVICE_ACTION = "action"
SERVICE_START_PROGRAM = "start_program"
SERVICE_STOP_PROGRAM = "stop_program"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Load Entities from the config settings."""
    coordinator: MieleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[MieleEntity] = []
    devices = coordinator.data
    for _, device in devices.items():
        entities.append(MieleDevice(coordinator, device))

    async_add_entities(entities, True)
    coordinator.remove_old_entities(Platform.DEVICE_TRACKER)  # Probably not needed.

    # Register the Services
    hass.services.async_register(
        DOMAIN,
        SERVICE_ACTION,
        coordinator.service_action,
        vol.All(
            cv.has_at_least_one_key("entity_id", "device_id"),
            cv.has_at_most_one_key("entity_id", "device_id"),
            cv.make_entity_service_schema(
                {
                    vol.Optional("entity_id"): cv.comp_entity_ids,
                    vol.Optional("device_id"): cv.string,
                    vol.Required("body"): cv.string,
                }
            ),
        ),
    )

    # Service Trigger Moved to coordinator to be able to get registry.
    hass.services.async_register(
        DOMAIN,
        SERVICE_START_PROGRAM,
        coordinator.service_action,
        vol.All(
            cv.has_at_least_one_key("entity_id", "device_id"),
            cv.has_at_most_one_key("entity_id", "device_id"),
            cv.make_entity_service_schema(
                {
                    vol.Optional("entity_id"): cv.comp_entity_ids,
                    vol.Optional("device_id"): cv.string,
                    vol.Required("program_id"): vol.Coerce(int),
                }
            ),
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_PROGRAM,
        coordinator.service_action,
        vol.All(
            cv.has_at_least_one_key("entity_id", "device_id"),
            cv.has_at_most_one_key("entity_id", "device_id"),
            cv.make_entity_service_schema(
                {
                    vol.Optional("entity_id"): cv.comp_entity_ids,
                    vol.Optional("device_id"): cv.string,
                }
            ),
        ),
    )


class MieleDevice(MieleEntity, ScannerEntity):
    """Miele Device, for Automation Services."""

    def __init__(
        self,
        coordinator: MieleDataUpdateCoordinator,
        device: dict[str, any],
    ):
        """Initialise Miele Device Entity."""
        super().__init__(coordinator, DOMAIN, device)
        self._attr_icon = "mdi:play"

    @property
    def source_type(self) -> SourceType | str:
        """Return the source type, eg gps or router, of the device."""
        return slugify(self._attr_name)

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
        await self.coordinator.client.action(self.device_id, action)

    async def start_program(self, program_id):
        """Start Program on Device."""
        await self.coordinator.client.start_program(self.device_id, program_id)

    async def stop_program(self):
        """Stop program action."""
        body = {"processAction": 2}
        await self.action(body)
