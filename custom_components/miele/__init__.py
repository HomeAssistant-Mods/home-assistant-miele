"""Miele@home Device Support."""

import logging
import os

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
from homeassistant.helpers.entity_registry import async_get
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_implementations,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.util import slugify

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, ENTITIES
from .coordinator import MieleDataUpdateCoordinator

_LOGGER: logging.Logger = logging.getLogger(__name__)

CONF_CACHE_PATH = "cache_path"


async def async_setup(hass: HomeAssistant, config: Config):
    """Initiate the Migraiton of the YAML setup to User Interface."""
    if conf := config.get(DOMAIN):
        # Delete cache-path
        cache = config[DOMAIN].get(
            CONF_CACHE_PATH, hass.config.path(STORAGE_DIR, ".miele-token-cache")
        )
        if cache:
            try:
                os.remove(cache)
            except OSError:
                _LOGGER.warn("Couldn't delte token cache to %s", cache)
                pass

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
        entry.entry_id,
    )
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()

    # Clean Up Device Entities so they can be re-written.
    # e.g. miele.washing_machine.
    #
    # Miele Device has been moved to Device Tracker.
    entity_registry = async_get(hass)
    for _, device in coordinator.data.items():
        ident = device["ident"]
        name = ident["deviceName"]
        if len(name) == 0:
            name = f"{ident['type']['value_localized']}"

        entity = entity_registry.async_get(f"{DOMAIN}.{slugify(name)}")
        if entity and not entity.config_entry_id:
            _LOGGER.debug("Migrating: %s", entity.entity_id)
            entity_registry.async_remove(entity.entity_id)

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
