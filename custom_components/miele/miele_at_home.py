"""Miele@home Client API."""

import json
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
                _LOGGER.debug("Failed to retrieve devices: %s", devices.status)
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

    async def action(self, device_id, body):
        """Perform an Action on the Miele Device."""
        _LOGGER.debug(f"Executing device action for {device_id}{body}")
        try:
            headers = {"Content-Type": "application/json"}
            result = await self._session.async_request(
                "put",
                self.ACTION_URL.format(device_id),
                data=json.dumps(body),
                headers=headers,
            )

            if result.status != 200:
                match result.status:
                    case 401:
                        _LOGGER.info("Request unauthorized, re-auth required.")
                    case _:
                        _LOGGER.error(
                            "Failed to execute device action for %s: %s %s",
                            device_id,
                            result.status,
                            result.json(),
                        )

                return None

            return result.json()
        except ConnectionError as err:
            _LOGGER.error(f"Failed to execute device action: {err}")
            return None

    async def start_program(self, device_id, program_id):
        """Start a Program."""
        _LOGGER.debug(f"Starting program {program_id} for {device_id}")
        try:
            headers = {"Content-Type": "application/json"}
            result = await self._session.async_request(
                "put",
                self.PROGRAMS_URL.format(device_id),
                data=json.dumps({"programId": program_id}),
                headers=headers,
            )

            if result.status != 200:
                match result.status:
                    case 401:
                        _LOGGER.info("Request unauthorized, re-auth required.")
                    case _:
                        _LOGGER.error(
                            "Failed to execute device action for %s: %s %s",
                            device_id,
                            result.status,
                            result.json(),
                        )

                return None

            return result.json()
        except ConnectionError as err:
            _LOGGER.error(f"Failed to execute start program: {err}")
            return None
