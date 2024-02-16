"""Config flow for Miele@home."""

import logging
import voluptuous as vol

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    OptionsFlow,
    FlowResult,
    CONN_CLASS_CLOUD_POLL,
)
from homeassistant.const import CONF_LANGUAGE, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow, selector

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


class MieleOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Miele@home OAuth2 authentication."""

    # Used to call the migration method if the verison changes.
    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL
    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Set up instance."""
        super().__init__()
        self._reauth_entry: ConfigEntry | None = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    async def async_step_import(
        self, config: dict[str, Any] | None = None
    ) -> FlowResult:
        """Start a configuration flow based on imported data."""
        await self._async_handle_discovery_without_unique_id()
        self.async_oauth_create_entry()

        return await self.async_step_user()

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Perform reauth upon an API authentication error."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm reauth dialog."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")

        return await self.async_step_user()

    async def async_oauth_create_entry(
        self, data: dict[str, Any] | None = None
    ) -> FlowResult:
        """Create an entry for Miele."""
        existing_entry = await self.async_set_unique_id(DOMAIN)

        if existing_entry:
            self.hass.config_entries.async_update_entry(existing_entry, data=data)
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        entry: FlowResult = await super().async_oauth_create_entry(data)

        # Set Initial Options from yaml if available, for migration.
        init_data: dict = self.init_data
        if init_data:
            entry["options"][CONF_LANGUAGE] = init_data.get(
                "lang", self.hass.config.language
            )
            entry["options"][CONF_SCAN_INTERVAL] = self.init_data.get(
                "interval", DEFAULT_SCAN_INTERVAL
            )

        return entry

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the option flow handler."""
        return MieleOptionsFlowHandler(config_entry)


class MieleOptionsFlowHandler(OptionsFlow):
    """Miele config options flow handler."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,  # pylint: disable=unused-argument
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=60,
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Required(
                        CONF_LANGUAGE,
                        default=self.options.get(
                            CONF_LANGUAGE, self.hass.config.language
                        ),
                    ): selector.LanguageSelector(
                        selector.LanguageSelectorConfig(),
                    ),
                },
            ),
        )

    async def _update_options(self) -> FlowResult:
        """Update config entry options."""
        return self.async_create_entry(title=self.config_entry.title, data=self.options)
