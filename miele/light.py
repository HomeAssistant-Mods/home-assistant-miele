import logging

from datetime import timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.components.light import Light

from custom_components.miele import DOMAIN as MIELE_DOMAIN, DATA_CLIENT, DATA_DEVICES

PLATFORMS = ['miele']

_LOGGER = logging.getLogger(__name__)

ALL_DEVICES = []

SUPPORTED_TYPES = [ 17, 18, 32, 33, 34, 68 ]

# pylint: disable=W0612
def setup_platform(hass, config, add_devices, discovery_info=None):
    
    global ALL_DEVICES

    devices = hass.data[MIELE_DOMAIN][DATA_DEVICES]
    for k, device in devices.items():
        device_type = device['ident']['type']

        light_devices = []
        if device_type['value_raw'] in SUPPORTED_TYPES:
            light_devices.append(MieleLight(hass, device))

        add_devices(light_devices)
        ALL_DEVICES = ALL_DEVICES + light_devices

def update_device_state():
    for device in ALL_DEVICES:
        device.async_schedule_update_ha_state(True)

class MieleLight(Light):
    def __init__(self, hass, device):
        self._hass = hass
        self._device = device
        self._ha_key = 'light'

    @property
    def device_id(self):
        """Return the unique ID for this light."""
        return self._device['ident']['deviceIdentLabel']['fabNumber']

    @property
    def unique_id(self):
        """Return the unique ID for this light."""
        return self.device_id + '_' + self._ha_key

    @property
    def name(self):
        """Return the name of the light."""
        ident = self._device['ident']
        
        result = ident['deviceName']
        if len(result) == 0:
            return ident['type']['value_localized'] + ' ' + self._ha_key
        else:
            return result + ' ' + self._ha_key

    @property
    def is_on(self):
        """Return the state of the light."""
        return self._device['state']['light'] == 1  

    def turn_on(self, **kwargs):
        service_parameters = {
            'device_id': self.device_id,
            'body': { 'light': 1 }
        }
        self._hass.services.call(MIELE_DOMAIN, 'action', service_parameters)

    def turn_off(self, **kwargs):
        service_parameters = {
            'device_id': self.device_id,
            'body': { 'light': 2 }
        }
        self._hass.services.call(MIELE_DOMAIN, 'action', service_parameters)

    async def async_update(self): 
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.error('Miele device not found: {}'.format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]
