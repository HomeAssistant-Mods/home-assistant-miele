"""Helper and wrapper classes for Miele@home module."""

import logging

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

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
    ):
        """Initialise the Miele@home Update Coordinator class."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

        self._language = language
        self._session = session
        self._client = MieleClient(hass, session)

    def _to_dict(self, items: list) -> dict:
        """Replace with Dict."""
        result = {}
        for item in items:
            ident = item["ident"]
            result[ident["deviceIdentLabel"]["fabNumber"]] = item

        return result

    async def _async_update_data(self) -> dict:
        """Refresh the data from the API endpoint and process."""
        device_state = await self._client.get_devices(self._language)
        device_data = {}

        if device_state is None:
            _LOGGER.error("Did not receive Miele devices")
            raise UpdateFailed("Did not receive Miele devices.")
        else:
            device_data = self._to_dict(device_state)

            # for device in DEVICES:
            #    device.async_schedule_update_ha_state(True)

            # for component in MIELE_COMPONENTS:
            #    platform = import_module(".{}".format(component), __name__)
            #    platform.update_device_state()

        return device_data
