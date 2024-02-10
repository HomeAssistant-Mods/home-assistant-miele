"""Miele base entities."""

import logging

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import MieleDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MieleEntity(CoordinatorEntity[MieleDataUpdateCoordinator]):
    """Miele based Entity."""

    def __init__(
        self,
        coordinator: MieleDataUpdateCoordinator,
        device: dict[str, any],
        key: str,
        key_name: str | None = None,
    ):
        """Initialize class properties."""
        super().__init__(coordinator)
        self._device = device
        self._key = key

        self.device_id = self._device["ident"]["deviceIdentLabel"]["fabNumber"]
        self.unique_id = f"{self.device_id}_{self._key}"

        ident = self._device["ident"]
        name = ident["deviceName"]
        if len(name) == 0:
            name = f"{ident['type']['value_localized']}"

        if key_name:
            self.name = f"{name} {key_name}"
        else:
            self.name = name

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device_info of the device."""
        ident = self._device["ident"]

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

    async def async_update(self) -> None:
        """Perform an Update and Check if Device Available."""
        await super().async_update()

        if self.device_id not in self.coordinator.data:
            _LOGGER.debug(f"Miele device disappeared: {self.device_id}")
        else:
            self._device = self.coordinator.data[self.device_id]
