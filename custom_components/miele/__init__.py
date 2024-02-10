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
)
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_implementations,
    async_get_config_entry_implementation,
)
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
        # TODO: Delete cache-path

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
                    DOMAIN,
                    context={"source": SOURCE_IMPORT},
                    data=conf,
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
