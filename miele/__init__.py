"""
Support for Miele.
"""
import asyncio
import logging

from datetime import timedelta

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.loader import get_platform
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.helpers.config_validation as cv

from .miele_at_home import MieleClient, MieleOAuth

REQUIREMENTS = ['requests_oauthlib']

DEPENDENCIES = ['http']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Miele@home'
DOMAIN = 'miele'
DATA_OAUTH = 'oauth'
DATA_CONFIG = 'config'
DATA_DEVICES = 'devices'
SCOPE = 'code'
DEFAULT_CACHE_PATH = '.miele-token-cache'
DEFAULT_LANG = 'en'
AUTH_CALLBACK_PATH = '/api/miele'
AUTH_CALLBACK_NAME = 'api:miele'
CONF_CLIENT_ID = 'client_id'
CONF_CLIENT_SECRET = 'client_secret'
CONF_LANG = 'lang'
CONF_CACHE_PATH = 'cache_path'
CONFIGURATOR_LINK_NAME = 'Link Miele account'
CONFIGURATOR_SUBMIT_CAPTION = 'I authorized successfully'
CONFIGURATOR_DESCRIPTION = 'To link your Miele account, ' \
'click the link, login, and authorize:'

MIELE_COMPONENTS = ['binary_sensor', 'sensor']

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_CLIENT_SECRET): cv.string,
        vol.Optional(CONF_LANG): cv.string,
        vol.Optional(CONF_CACHE_PATH): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)

def request_configuration(hass, config, oauth):
    """Request Miele authorization."""
    configurator = hass.components.configurator
    hass.data[DOMAIN][DATA_CONFIG] = configurator.async_request_config(
        DEFAULT_NAME, lambda _: None,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=oauth.authorization_url,
        description=CONFIGURATOR_DESCRIPTION,
        submit_caption=CONFIGURATOR_SUBMIT_CAPTION)
    return

def create_sensor(client, hass, home_device, lang):
    return MieleDevice(hass, client, home_device, lang)

def _to_dict(items):
    # Replace with map()
    result = {}
    for item in items:
        ident = item['ident']
        result[ident['deviceIdentLabel']['fabNumber']] = item

    return result

async def async_setup(hass, config):
    """Set up the Miele platform."""

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if DATA_OAUTH not in hass.data[DOMAIN]:
        callback_url = '{}{}'.format(hass.config.api.base_url, AUTH_CALLBACK_PATH)
        cache = config[DOMAIN].get(CONF_CACHE_PATH, hass.config.path(DEFAULT_CACHE_PATH))
        hass.data[DOMAIN][DATA_OAUTH] = MieleOAuth(
            config[DOMAIN].get(CONF_CLIENT_ID), config[DOMAIN].get(CONF_CLIENT_SECRET), 
            redirect_uri=callback_url,
            cache_path=cache)

    if not hass.data[DOMAIN][DATA_OAUTH].authorized:
        _LOGGER.info('no token; requesting authorization')
        hass.http.register_view(MieleAuthCallbackView(config, hass.data[DOMAIN][DATA_OAUTH]))
        request_configuration(hass, config, hass.data[DOMAIN][DATA_OAUTH])
        return True

    if DATA_CONFIG in hass.data[DOMAIN]:
        configurator = hass.components.configurator
        configurator.async_request_done(hass.data[DOMAIN][DATA_CONFIG])
        del hass.data[DOMAIN][DATA_CONFIG]

    lang = config[DOMAIN].get(CONF_LANG, DEFAULT_LANG)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    client = MieleClient(hass.data[DOMAIN][DATA_OAUTH])
    hass.data[DOMAIN][DATA_DEVICES] = _to_dict(client.get_devices(lang))

    devices = [create_sensor(client, hass, home_device, lang) for k, home_device in hass.data[DOMAIN][DATA_DEVICES].items()]
    await component.async_add_entities(devices, False)
    
    for component in MIELE_COMPONENTS:
        load_platform(hass, component, DOMAIN, {}, config)

    def refresh_devices(event_time):
        _LOGGER.debug("Attempting to update Miele devices")
        device_state = client.get_devices()
        if device_state is None:
            _LOGGER.error("Did not receive Miele devices")
        else:
            hass.data[DOMAIN][DATA_DEVICES] = _to_dict(device_state)
            for device in devices:
               device.async_schedule_update_ha_state(True)

            for component in MIELE_COMPONENTS:
                platform = get_platform(hass, component, DOMAIN)
                platform.update_device_state()

    interval = timedelta(seconds=5)
    async_track_time_interval(hass, refresh_devices, interval)

    return True


class MieleAuthCallbackView(HomeAssistantView):
    """Miele Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME

    def __init__(self, config, oauth):
        """Initialize."""
        self.config = config
        self.oauth = oauth

    @callback
    def get(self, request):
        """Receive authorization token."""
        hass = request.app['hass']

        self.oauth.get_access_token(request.query['code'])
        hass.async_add_job(async_setup, hass, self.config)

class MieleDevice(Entity):
    def __init__(self, hass, client, home_device, lang):
        self._hass = hass
        self._client = client
        self._home_device = home_device
        self._lang = lang

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self._home_device['ident']['deviceIdentLabel']['fabNumber']

    @property
    def name(self):
        """Return the name of the sensor."""

        ident = self._home_device['ident']
        
        result = ident['deviceName']
        if len(result) == 0:
            result = ident['type']['value_localized']

        return result

    @property
    def state(self):
        """Return the state of the sensor."""

        result = self._home_device['state']['status']['value_localized']
        if result == None:
            result = self._home_device['state']['status']['value_raw']

        return result

    @property
    def device_state_attributes(self):
        """Attributes."""

        result = {}
        result['state_raw'] = self._home_device['state']['status']['value_raw']

        result['model'] = self._home_device['ident']['deviceIdentLabel']['techType']
        result['device_type'] = self._home_device['ident']['type']['value_localized']
        result['fabrication_number'] = self._home_device['ident']['deviceIdentLabel']['fabNumber']

        result['gateway_type'] = self._home_device['ident']['xkmIdentLabel']['techType']
        result['gateway_version'] = self._home_device['ident']['xkmIdentLabel']['releaseVersion']
        
        return result

    async def async_update(self):        
        if not self.unique_id in self._hass.data[DOMAIN][DATA_DEVICES]:
            _LOGGER.error('Miele device not found: {}'.format(self.unique_id))
        else:
            self._home_device = self._hass.data[DOMAIN][DATA_DEVICES][self.unique_id]
