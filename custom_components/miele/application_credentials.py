"""Miele Application Credentials Setup."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.components import http
from homeassistant.components.application_credentials import (
    AuthImplementation,
    AuthorizationServer,
    ClientCredential,
)

from .const import OAUTH_AUTHORIZE_URL, OAUTH_TOKEN_URL

HEADER_FRONTEND_BASE = "HA-Frontend-Base"
AUTH_CALLBACK_PATH = "/auth/external/callback"


class OAuth2Impl(AuthImplementation):
    """Custom OAuth2 implementation."""

    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri, ignore my.homeassistant callback."""
        if (req := http.current_request.get()) is None:
            raise RuntimeError("No current request in context")

        if (ha_host := req.headers.get(HEADER_FRONTEND_BASE)) is None:
            raise RuntimeError("No header in request")

        return f"{ha_host}{AUTH_CALLBACK_PATH}"


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return authorization server."""
    return AuthorizationServer(
        authorize_url=OAUTH_AUTHORIZE_URL, token_url=OAUTH_TOKEN_URL
    )


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return auth implementation for a custom auth implementation."""
    return OAuth2Impl(
        hass,
        auth_domain=auth_domain,
        credential=credential,
        authorization_server=await async_get_authorization_server(hass),
    )
