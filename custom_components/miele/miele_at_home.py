"""Miele@home API."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

_LOGGER = logging.getLogger(__name__)


class MieleClient:
    """Miele@home client class."""

    DEVICES_URL = "https://api.mcs3.miele.com/v1/devices"
    ACTION_URL = "https://api.mcs3.miele.com/v1/devices/{0}/actions"
    PROGRAMS_URL = "https://api.mcs3.miele.com/v1/devices/{0}/programs"

    def __init__(self, hass: HomeAssistant, session: OAuth2Session):
        """Initialse class."""
        self._session = session
        self.hass = hass

    async def _get_devices_raw(self, lang: str) -> dict | None:
        """Get the Devices from the API."""
        _LOGGER.debug("Requesting Miele device update")
        try:
            # Token Refresh is built in to the async_request.
            devices = await self._session.async_request(
                "get", self.DEVICES_URL, params={"language": lang}
            )

            if devices.status != 200:
                _LOGGER.debug("Failed to retrieve devices: %s", devices.status_code)
                return None

            return await devices.json()
        except ConnectionError as err:
            _LOGGER.error(f"Failed to retrieve Miele devices: {err}")
            return None

    async def get_devices(self, lang: str = "en") -> list | None:
        """Get Miele Devices."""
        home_devices = await self._get_devices_raw(lang)
        if home_devices is None:
            return None

        result = []
        for home_device in home_devices:
            result.append(home_devices[home_device])

        return result
