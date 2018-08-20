"""
Support for Miele.
"""
import asyncio
import json
import logging

from datetime import timedelta

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.const import STATE_UNKNOWN, STATE_ON, STATE_OFF
import homeassistant.helpers.config_validation as cv

from requests_oauthlib import OAuth2Session

from .miele_const import *
from .miele_utils import DeviceState, get_converter

REQUIREMENTS = ['requests_oauthlib']

DEPENDENCIES = ['http']

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ['sensor']

STATE_MAP = {
    DeviceState.UNKNOWN: STATE_UNKNOWN,
    DeviceState.OFF: STATE_OFF,
    DeviceState.STAND_BY: STATE_ON,
    DeviceState.RUNNING: STATE_ON,
    DeviceState.PROGRAMMED: STATE_ON,
    DeviceState.PAUSED: STATE_ON,
    DeviceState.END: STATE_ON,
    DeviceState.SERVICE: STATE_ON,
    DeviceState.NOT_CONNECTED: STATE_OFF,
}

DEFAULT_NAME = 'Miele@home'
DOMAIN = 'miele'
DATA_OAUTH = 'oauth'
DATA_CONFIG = 'config'
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

SCAN_INTERVAL = timedelta(seconds=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CLIENT_ID): cv.string,
    vol.Required(CONF_CLIENT_SECRET): cv.string,
    vol.Optional(CONF_LANG): cv.string,
    vol.Optional(CONF_CACHE_PATH): cv.string,
})

def request_configuration(hass, config, add_devices, oauth):
    """Request Miele authorization."""
    configurator = hass.components.configurator
    hass.data[DOMAIN][DATA_CONFIG] = configurator.request_config(
        DEFAULT_NAME, lambda _: None,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=oauth.authorization_url('https://api.mcs3.miele.com/thirdparty/login', 
            state='login'),
        description=CONFIGURATOR_DESCRIPTION,
        submit_caption=CONFIGURATOR_SUBMIT_CAPTION)

def map_miele_state(state):
    if state in STATE_MAP:
        return STATE_MAP[state]
    else:
        _LOGGER.error("Unmapped DeviceState %s", state.name)
        return state.name

def create_sensor(session, home_device, lang):
    return MieleSensor(session, home_device, lang)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Miele platform."""

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if DATA_OAUTH not in hass.data[DOMAIN]:
        callback_url = '{}{}'.format(hass.config.api.base_url, AUTH_CALLBACK_PATH)
        
        cache = config.get(CONF_CACHE_PATH, hass.config.path(DEFAULT_CACHE_PATH))
        token = _get_cached_token(cache)

        hass.data[DOMAIN][DATA_OAUTH] = OAuth2Session(config.get(CONF_CLIENT_ID), 
            auto_refresh_url='https://api.mcs3.miele.com/thirdparty/token',
            redirect_uri=callback_url, token=token)

    if not hass.data[DOMAIN][DATA_OAUTH].authorized:
        _LOGGER.info('no token; requesting authorization')
        hass.http.register_view(MieleAuthCallbackView(config, add_devices, hass.data[DOMAIN][DATA_OAUTH]))
        request_configuration(hass, config, add_devices, hass.data[DOMAIN][DATA_OAUTH])
        return

    if DATA_CONFIG in hass.data[DOMAIN]:
        configurator = hass.components.configurator
        configurator.request_done(hass.data[DOMAIN][DATA_CONFIG])
        del hass.data[DOMAIN][DATA_CONFIG]

    lang = config.get(CONF_LANG, DEFAULT_LANG)
    add_devices([create_sensor(hass.data[DOMAIN][DATA_OAUTH], home_device, lang) for home_device in get_devices(hass.data[DOMAIN][DATA_OAUTH], lang)], True)

def get_devices(session, lang):
    devices = session.get('https://api.mcs3.miele.com/v1/devices', params={'language':lang})
    if devices.status_code != 200:
        _LOGGER.error(f'Failed to retrieve devices: {devices.status_code}')

    home_devices = devices.json()

    result = []
    for home_device in home_devices:
        result.append(home_devices[home_device])

    return result   

class MieleAuthCallbackView(HomeAssistantView):
    """Miele Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME

    def __init__(self, config, add_devices, oauth):
        """Initialize."""
        self.config = config
        self.add_devices = add_devices
        self.oauth = oauth

    @callback
    def get(self, request):
        """Receive authorization token."""
        hass = request.app['hass']

        token = self.oauth.fetch_token('https://api.mcs3.miele.com/thirdparty/token',
            code=request.query['code'],
            client_secret=self.config.get(CONF_CLIENT_SECRET))

        cache = self.config.get(CONF_CACHE_PATH, hass.config.path(DEFAULT_CACHE_PATH))
        _save_token(cache, token)

        hass.async_add_job(setup_platform, hass, self.config, self.add_devices)

def _get_cached_token(cache_path):

    token = None
    if cache_path:
        try:
            f = open(cache_path)
            token_info_string = f.read()
            f.close()
            token = json.loads(token_info_string)

        except IOError:
            pass
    
    return token

def _save_token(cache_path, token):
    if cache_path:
        try:
            f = open(cache_path, 'w')
            f.write(json.dumps(token))
            f.close()
        except IOError:
            _LOGGER._warn(f'Couldn\'t write token cache to {cache_path}')
            pass

class MieleSensor(Entity):
    def __init__(self, session, home_device, lang):
        self._session = session
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
        try:
            state = DeviceState(self._home_device['state']['status']['value_raw'])
            return map_miele_state(state)
        except KeyError:
            return map_miele_state(DeviceState.UNKNOWN)

    @property
    def device_state_attributes(self):
        """Attributes."""

        result = {}
        for key in self._home_device['state']:
            prop = self._home_device['state'][key]
            
            if key == MIELE_TEMPERATURE or key == MIELE_TARGET_TEMPERATURE:
                i = 0
                for item in prop:
                    value = get_converter(key)(item)
                    result[f'{key}_{i}'] = value
                    i = i+1

            else:
                value = get_converter(key)(prop)
                result[key] = value

        return result

    def update(self):
        _LOGGER.info(f'Updating Miele {self.unique_id}')
        state = self._session.get(f'https://api.mcs3.miele.com/v1/devices/{self.unique_id}/state', params={'language':self._lang})
        if state.status_code != 200:
            _LOGGER.error(f'Failed to retrieve devices: {state.status_code}')

        self._home_device['state'] = state.json()
        return
