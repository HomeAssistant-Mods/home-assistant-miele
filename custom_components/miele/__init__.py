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
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_implementations,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.storage import STORAGE_DIR

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, ENTITIES
from .coordinator import MieleDataUpdateCoordinator
from .entity import MieleEntity

_LOGGER: logging.Logger = logging.getLogger(__name__)

CONF_CACHE_PATH = "cache_path"

DEVICES = []

SERVICE_ACTION = "action"
SERVICE_START_PROGRAM = "start_program"
SERVICE_STOP_PROGRAM = "stop_program"


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

    await hass.config_entries.async_forward_entry_setups(entry, ENTITIES)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Setup the Main Miele Device for services, and migration
    # No idea how to add to the Config Entry of Miele.
    DEVICES = []
    DEVICES.extend(
        [MieleDevice(coordinator, device) for _, device in coordinator.data.items()]
    )
    component = EntityComponent(
        _LOGGER,
        DOMAIN,
        hass,
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    await component.async_add_entities(DEVICES, False)

    # Register the Services
    register_services(hass)

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


def register_services(hass):
    """Register all services for Miele devices."""
    hass.services.async_register(DOMAIN, SERVICE_ACTION, _action_service)
    hass.services.async_register(DOMAIN, SERVICE_START_PROGRAM, _action_start_program)
    hass.services.async_register(DOMAIN, SERVICE_STOP_PROGRAM, _action_stop_program)


async def _apply_service(service, service_func, *service_func_args):
    entity_ids = service.data.get("entity_id")

    _devices = []
    if entity_ids:
        _devices.extend(
            [device for device in DEVICES if device.entity_id in entity_ids]
        )

    device_ids = service.data.get("device_id")
    if device_ids:
        _devices.extend(
            [device for device in DEVICES if device.unique_id in device_ids]
        )

    for device in _devices:
        await service_func(device, *service_func_args)


async def _action_service(service):
    body = service.data.get("body")
    await _apply_service(service, MieleDevice.action, body)


async def _action_start_program(service):
    program_id = service.data.get("program_id")
    await _apply_service(service, MieleDevice.start_program, program_id)


async def _action_stop_program(service):
    body = {"processAction": 2}
    await _apply_service(service, MieleDevice.action, body)


class MieleDevice(MieleEntity):
    """Miele Device, for Automation Services."""

    def __init__(
        self,
        coordinator: MieleDataUpdateCoordinator,
        device: dict[str, any],
    ):
        """Initialise Miele Device Entity."""
        super().__init__(coordinator, DOMAIN, device)

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
        await self.coordinator.client.action(self.unique_id, action)

    async def start_program(self, program_id):
        """Start Program on Device."""
        await self.coordinator.client.start_program(self.unique_id, program_id)
