import logging

from datetime import timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.components.binary_sensor import BinarySensorDevice

from custom_components.miele import DOMAIN as MIELE_DOMAIN, DATA_CLIENT

PLATFORMS = ['miele']

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)

def setup_platform(hass, config, add_devices, discovery_info=None):
    
    client = hass.data[MIELE_DOMAIN][DATA_CLIENT]
    devices = client.get_devices()
    for device in devices:
        device_state = device['state']

        binary_devices = []
        if 'signalInfo' in device_state:
            binary_devices.append(MieleBinarySensor(device, client, 'signalInfo', 'Info'))
        if 'signalFailure' in device_state:
            binary_devices.append(MieleBinarySensor(device, client, 'signalFailure', 'Failure'))
        if 'signalDoor' in device_state:
            binary_devices.append(MieleBinarySensor(device, client, 'signalDoor', 'Door'))

        add_devices(binary_devices)


class MieleBinarySensor(BinarySensorDevice):

    def __init__(self, device, client, key, ha_key):
        self._client = client
        self._device = device
        self._key = key
        self._ha_key = ha_key

    @property
    def device_id(self):
        """Return the unique ID for this sensor."""
        return self._device['ident']['deviceIdentLabel']['fabNumber']

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self.device_id + '_' + self._ha_key

    @property
    def name(self):
        """Return the name of the sensor."""
        ident = self._device['ident']
        
        result = ident['deviceName']
        if len(result) == 0:
            return ident['type']['value_localized'] + ' ' + self._ha_key
        else:
            return result + ' ' + self._ha_key

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return bool(self._device['state'][self._key])

    @property
    def device_class(self):
        if self._key == 'signalDoor':
            return 'door'
        else:
            return 'problem'

    def update(self): 
        # _LOGGER.info(f'Updating Miele Binary Sensor {self.unique_id}')
        self._device = self._client.get_device(self.device_id)
        return