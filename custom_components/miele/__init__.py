"""Miele@home Device Support."""
import logging

from aiohttp.client_exceptions import ClientError, ClientResponseError

from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_SCAN_INTERVAL,
    CONF_LANGUAGE,
    CONF_DEVICES,
)
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_implementations,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, ENTITIES
from .coordinator import MieleDataUpdateCoordinator


_LOGGER: logging.Logger = logging.getLogger(__name__)

DEVICES = []
DATA_CLIENT = "client"
DATA_DEVICES = "devices"

MIELE_COMPONENTS = ["binary_sensor", "light", "sensor", "fan"]

SERVICE_ACTION = "action"
SERVICE_START_PROGRAM = "start_program"
SERVICE_STOP_PROGRAM = "stop_program"


async def async_setup(hass: HomeAssistant, config: Config):
    """Initiate the Migraiton of the YAML setup to User Interface."""
    if conf := config.get(DOMAIN):
        # Import the Client Credentials, if not imported.
        implementation = await async_get_implementations(hass, DOMAIN)
        if not implementation:
            if CONF_CLIENT_ID in conf and CONF_CLIENT_SECRET in conf:
                await async_import_client_credential(
                    hass,
                    DOMAIN,
                    ClientCredential(
                        conf[CONF_CLIENT_ID],
                        conf[CONF_CLIENT_SECRET],
                        "miele",
                    ),
                )

        # Raise the relevant issue to migrate or just remove the YAML entries.
        if DOMAIN not in hass.config_entries.async_domains():
            async_create_issue(
                hass,
                DOMAIN,
                DOMAIN,
                is_fixable=True,
                severity=IssueSeverity.WARNING,
                translation_key="deprecated_yaml_migrate",
                translation_placeholders={
                    "domain": DOMAIN,
                    "integration_title": "Miele@home",
                },
            )

            # Initiate the Migraiton Import.
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}
                )
            )
        else:
            async_create_issue(
                hass,
                DOMAIN,
                DOMAIN,
                is_fixable=True,
                severity=IssueSeverity.WARNING,
                translation_key="deprecated_yaml_config",
                translation_placeholders={
                    "domain": DOMAIN,
                    "integration_title": "Miele@home",
                },
            )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Miele@home integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get Session and validate token is valid.
    implementation = await async_get_config_entry_implementation(hass, entry)
    session = OAuth2Session(hass, entry, implementation)
    try:
        await session.async_ensure_token_valid()
    except ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed(
                "OAuth session is not valid, reauth required"
            ) from err
        raise ConfigEntryNotReady from err
    except ClientError as err:
        raise ConfigEntryNotReady from err

    coordinator = MieleDataUpdateCoordinator(
        hass,
        session,
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        entry.options.get(CONF_LANGUAGE, hass.config.language),
    )
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, ENTITIES)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, ENTITIES):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class MieleDevice(Entity):
    """A Miele Device Entity."""

    def __init__(self, hass, client, home_device, lang):
        """Initialize the entity."""
        self._hass = hass
        self._client = client
        self._home_device = home_device
        self._lang = lang

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self._home_device["ident"]["deviceIdentLabel"]["fabNumber"]

    @property
    def name(self):
        """Return the name of the sensor."""

        ident = self._home_device["ident"]

        result = ident["deviceName"]
        if len(result) == 0:
            result = ident["type"]["value_localized"]

        return result

    @property
    def state(self):
        """Return the state of the sensor."""

        result = self._home_device["state"]["status"]["value_localized"]
        if result == None:
            result = self._home_device["state"]["status"]["value_raw"]

        return result

    @property
    def extra_state_attributes(self):
        """Attributes."""

        result = {}
        result["state_raw"] = self._home_device["state"]["status"]["value_raw"]

        result["model"] = self._home_device["ident"]["deviceIdentLabel"]["techType"]
        result["device_type"] = self._home_device["ident"]["type"]["value_localized"]
        result["fabrication_number"] = self._home_device["ident"]["deviceIdentLabel"][
            "fabNumber"
        ]

        result["gateway_type"] = self._home_device["ident"]["xkmIdentLabel"]["techType"]
        result["gateway_version"] = self._home_device["ident"]["xkmIdentLabel"][
            "releaseVersion"
        ]

        return result

    async def action(self, action):
        await self._client.action(self.unique_id, action)

    async def start_program(self, program_id):
        await self._client.start_program(self.unique_id, program_id)

    async def async_update(self):
        if not self.unique_id in self._hass.data[DOMAIN][CONF_DEVICES]:
            _LOGGER.debug("Miele device not found: {}".format(self.unique_id))
        else:
            self._home_device = self._hass.data[DOMAIN][CONF_DEVICES][self.unique_id]
