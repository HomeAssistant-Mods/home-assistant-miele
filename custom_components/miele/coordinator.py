"""Helper and wrapper classes for Miele@home module."""

import logging
import json

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from homeassistant.helpers.entity_registry import (
    async_get,
    async_entries_for_config_entry,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.service import ServiceCall


from .const import DOMAIN
from .miele_at_home import MieleClient

_LOGGER = logging.getLogger(__name__)


class MieleDataUpdateCoordinator(DataUpdateCoordinator):
    """Miele@home data updater."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: OAuth2Session,
        scan_interval: int,
        language: str,
        entry_id: str,
    ):
        """Initialise the Miele@home Update Coordinator class."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

        # Used outside of the Coordinator.
        self.client = MieleClient(hass, session)
        self.old_entries: dict[str, list[str]] = {}

        self._language = language
        self._session = session
        self._entity_registry = async_get(hass)
        self._entry_id = entry_id
        self._devices = []

        # Convert registries into Entity Platform and ID.
        registry_entries = async_entries_for_config_entry(
            self._entity_registry, self._entry_id
        )
        for reg_entity in registry_entries:
            if reg_entity.domain not in self.old_entries:
                self.old_entries[reg_entity.domain] = []
            self.old_entries[reg_entity.domain].append(reg_entity.entity_id)

    def _to_dict(self, items: list) -> dict:
        """Replace with Dict."""
        result = {}
        for item in items:
            ident = item["ident"]
            result[ident["deviceIdentLabel"]["fabNumber"]] = item

        return result

    async def _async_update_data(self) -> dict:
        """Refresh the data from the API endpoint and process."""
        result_data: dict[str, any] = {}
        if self.data:
            result_data = self.data

        device_state = await self.client.get_devices(self._language)

        if device_state is None:
            _LOGGER.error("Did not receive Miele devices")
            raise UpdateFailed("Did not receive Miele devices.")
        else:
            result_data.update(self._to_dict(device_state))

        return result_data

    def remove_old_entities(self, platform: str) -> None:
        """Remove old entities that are no longer provided."""
        if platform in self.old_entries:
            for entity_id in self.old_entries[platform]:
                _LOGGER.warning(
                    "Removing Old Entities for platform: %s, entity_id: %s",
                    platform,
                    entity_id,
                )
                self._entity_registry.async_remove(entity_id)

    async def service_action(self, service: ServiceCall):
        """Start Program Service, moved here but not ideal."""
        entity_ids = service.data.get("entity_id")
        device_ids = service.data.get("device_id")

        entities = self.hass.data["domain_entities"].get("device_tracker")
        _devices = []
        if entity_ids:
            _devices.extend(
                [
                    device
                    for device_id, device in entities.items()
                    if device_id in entity_ids
                ]
            )
        if device_ids:
            _devices.extend(
                [
                    device
                    for _, device in entities.items()
                    if device.device_id in device_ids
                ]
            )

        for device in _devices:
            match service.service:
                case "start_program":
                    await device.start_program(service.data.get("program_id"))
                case "stop_program":
                    await device.stop_program()
                case "action":
                    body = service.data.get("body")
                    if isinstance(body, str):
                        action = json.loads(body)
                    else:
                        action = body

                    await device.action(action)
                case _:
                    _LOGGER.warning("Service %s does not exist.", service.service)
