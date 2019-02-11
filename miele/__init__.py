"""
Support for Miele.
"""
import asyncio
import logging

from aiohttp import web
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

DEVICES = []

DEFAULT_NAME = 'Miele@home'
DOMAIN = 'miele'

_CONFIGURING = {}

DATA_OAUTH = 'oauth'
DATA_DEVICES = 'devices'
DATA_CLIENT = 'client'
SERVICE_ACTION = 'action'
SCOPE = 'code'
DEFAULT_CACHE_PATH = '.miele-token-cache'
DEFAULT_LANG = 'en'
AUTH_CALLBACK_PATH = '/api/miele/callback'
AUTH_CALLBACK_NAME = 'api:miele:callback'
CONF_CLIENT_ID = 'client_id'
CONF_CLIENT_SECRET = 'client_secret'
CONF_LANG = 'lang'
CONF_CACHE_PATH = 'cache_path'
CONFIGURATOR_LINK_NAME = 'Link Miele account'
CONFIGURATOR_SUBMIT_CAPTION = 'I have authorized Miele@home.'
CONFIGURATOR_DESCRIPTION = 'To link your Miele account, ' \
'click the link, login, and authorize:'
CONFIGURATOR_DESCRIPTION_IMAGE='https://api.mcs3.miele.com/images/miele-logo-immer-besser.svg'

MIELE_COMPONENTS = ['binary_sensor', 'light', 'sensor']

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
    async def miele_configuration_callback(callback_data):
        if not hass.data[DOMAIN][DATA_OAUTH].authorized:
            configurator.async_notify_errors(
                _CONFIGURING[DOMAIN],
                'Failed to register, please try again.')
            return

        if DOMAIN in _CONFIGURING:
            req_config = _CONFIGURING.pop(DOMAIN)
            hass.components.configurator.async_request_done(req_config)

        await async_setup(hass, config)

    configurator = hass.components.configurator
    _CONFIGURING[DOMAIN] = configurator.async_request_config(
        DEFAULT_NAME, 
        miele_configuration_callback,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=oauth.authorization_url,
        description=CONFIGURATOR_DESCRIPTION,
        description_image=CONFIGURATOR_DESCRIPTION_IMAGE,
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

    lang = config[DOMAIN].get(CONF_LANG, DEFAULT_LANG)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    client = MieleClient(hass.data[DOMAIN][DATA_OAUTH])
    hass.data[DOMAIN][DATA_CLIENT] = client
    hass.data[DOMAIN][DATA_DEVICES] = _to_dict(client.get_devices(lang))

    DEVICES.extend([create_sensor(client, hass, home_device, lang) for k, home_device in hass.data[DOMAIN][DATA_DEVICES].items()])
    await component.async_add_entities(DEVICES, False)
    
    for component in MIELE_COMPONENTS:
        load_platform(hass, component, DOMAIN, {}, config)

    def refresh_devices(event_time):
        _LOGGER.debug("Attempting to update Miele devices")
        device_state = client.get_devices(lang)
        if device_state is None:
            _LOGGER.error("Did not receive Miele devices")
        else:
            hass.data[DOMAIN][DATA_DEVICES] = _to_dict(device_state)
            for device in DEVICES:
               device.async_schedule_update_ha_state(True)

            for component in MIELE_COMPONENTS:
                platform = get_platform(hass, component, DOMAIN)
                platform.update_device_state()

    register_services(hass)

    interval = timedelta(seconds=5)
    async_track_time_interval(hass, refresh_devices, interval)

    return True

def register_services(hass):
    """Register all services for Miele devices."""
    hass.services.async_register(
        DOMAIN, SERVICE_ACTION, _action_service)

async def _apply_service(service, service_func, *service_func_args):
    entity_ids = service.data.get('entity_id')

    _devices = []
    if entity_ids:
        _devices.extend([device for device in DEVICES
                         if device.entity_id in entity_ids])

    device_ids = service.data.get('device_id')
    if device_ids:
        _devices.extend([device for device in DEVICES
                         if device.unique_id in device_ids])

    for device in _devices:
        await service_func(device, *service_func_args)  

async def _action_service(service):
    body = service.data.get('body')
    await _apply_service(service, MieleDevice.action, body)

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

        from oauthlib.oauth2.rfc6749.errors import MismatchingStateError
        from oauthlib.oauth2.rfc6749.errors import MissingTokenError

        response_message = """Miele@home has been successfully authorized!
        You can close this window now!"""

        result = None
        if request.query.get('code') is not None:
            try:
                result = self.oauth.get_access_token(request.query['code'])
            except MissingTokenError as error:
                _LOGGER.error("Missing token: %s", error)
                response_message = """Something went wrong when
                attempting authenticating with Miele@home. The error
                encountered was {}. Please try again!""".format(error)
            except MismatchingStateError as error:
                _LOGGER.error("Mismatched state, CSRF error: %s", error)
                response_message = """Something went wrong when
                attempting authenticating with Miele@home. The error
                encountered was {}. Please try again!""".format(error)
        else:
            _LOGGER.error("Unknown error when authorizing")
            response_message = """Something went wrong when
                attempting authenticating with Miele@home.
                An unknown error occurred. Please try again!
                """

        html_response = """<html><head><title>Miele@home Auth</title></head>
        <body><h1>{}</h1></body></html>""".format(response_message)

        response = web.Response(
            body=html_response, content_type='text/html', status=200,
            headers=None)
        response.enable_compression()

        return response

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

    async def action(self, action):
        self._client.action(self.unique_id, action)

    async def async_update(self):        
        if not self.unique_id in self._hass.data[DOMAIN][DATA_DEVICES]:
            _LOGGER.error('Miele device not found: {}'.format(self.unique_id))
        else:
            self._home_device = self._hass.data[DOMAIN][DATA_DEVICES][self.unique_id]
