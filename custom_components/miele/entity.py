"""Miele base entities."""

import logging

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .coordinator import MieleDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MieleEntity(CoordinatorEntity[MieleDataUpdateCoordinator]):
    """Miele based Entity."""

    def __init__(
        self,
        coordinator: MieleDataUpdateCoordinator,
        entity_type: str,
        device: dict[str, any],
        key: str,
        key_name: str | None = None,
    ):
        """Initialize class properties."""
        super().__init__(coordinator)
        self._key = key

        self.device_id = device["ident"]["deviceIdentLabel"]["fabNumber"]
        self.unique_id = f"{self.device_id}_{self._key}"

        ident = self.device["ident"]
        name = ident["deviceName"]
        if len(name) == 0:
            name = f"{ident['type']['value_localized']}"

        if key_name:
            self.name = f"{name} {key_name}"
        else:
            self.name = name

        return

        self._attr_unique_id = slugify(self.name)
        self.entity_id = f"{entity_type}.{self._attr_unique_id}"

        # If the entity is found in existing entities, remove it.
        if entity_type in coordinator.old_entries:
            if self.entity_id in coordinator.old_entries[entity_type]:
                entity_ids: list[str] = coordinator.old_entries[entity_type]
                entity_index = entity_ids.index(self.entity_id)
                entity_ids.pop(entity_index)

    @property
    def device(self) -> dict[str, any]:
        """Get the current Device."""
        return self.coordinator.data[self.device_id]

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device_info of the device."""
        ident = self.device["ident"]

        # Get Device Details
        device_name = ident["deviceName"]
        if len(device_name) == 0:
            device_name = ident["type"]["value_localized"]

        name = device_name.title()
        model = ident["deviceIdentLabel"]["techType"]
        version = ident["xkmIdentLabel"]["releaseVersion"]

        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=name,
            model=model,
            manufacturer="Miele",
            sw_version=version,
            serial_number=self.device_id,
        )
