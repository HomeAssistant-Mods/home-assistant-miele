import logging

from datetime import timedelta

from homeassistant.helpers.entity import Entity

from custom_components.miele import DOMAIN as MIELE_DOMAIN, DATA_DEVICES

PLATFORMS = ['miele']

_LOGGER = logging.getLogger(__name__)

ALL_DEVICES = []

def _map_key(key):
    if key == 'status':
        return 'Status'
    elif key == 'programType':
        return 'Program Type'
    elif key == 'programPhase':
        return 'Program Phase'
    elif key == 'targetTemperature':
        return 'Target Temperature'
    elif key == 'temperature':
        return 'Temperature'
    elif key == 'remainingTime':
        return 'Remaining Time'
    elif key == 'elapsedTime':
        return 'Elapsed Time'
    elif key == 'startTime':
        return 'Start Time'

def setup_platform(hass, config, add_devices, discovery_info=None):
    global ALL_DEVICES
    
    devices = hass.data[MIELE_DOMAIN][DATA_DEVICES]
    for k, device in devices.items():
        device_state = device['state']

        sensors = []
        if 'status' in device_state:
            sensors.append(MieleLocalizedSensor(hass, device, 'status'))

        if 'programType' in device_state:
            sensors.append(MieleRawSensor(hass, device, 'programType'))
        if 'programPhase' in device_state:
            sensors.append(MieleRawSensor(hass, device, 'programPhase'))

        if 'targetTemperature' in device_state:
            for i, val in enumerate(device_state['targetTemperature']):
                sensors.append(MieleTemperatureSensor(hass, device, 'targetTemperature', i))
        if 'temperature' in device_state:
            for i, val in enumerate(device_state['temperature']):
                sensors.append(MieleTemperatureSensor(hass, device, 'temperature', i))

        if 'remainingTime' in device_state:
            sensors.append(MieleTimeSensor(hass, device, 'remainingTime'))
        if 'startTime' in device_state:
            sensors.append(MieleTimeSensor(hass, device, 'startTime'))
        if 'elapsedTime' in device_state:
            sensors.append(MieleTimeSensor(hass, device, 'elapsedTime'))

        add_devices(sensors)
        ALL_DEVICES = ALL_DEVICES + sensors

def update_device_state():
    for device in ALL_DEVICES:
        device.async_schedule_update_ha_state(True)

class MieleRawSensor(Entity):

    def __init__(self, hass, device, key):
        self._hass = hass
        self._device = device
        self._key = key

    @property
    def device_id(self):
        """Return the unique ID for this sensor."""
        return self._device['ident']['deviceIdentLabel']['fabNumber']

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self.device_id + '_' + self._key

    @property
    def name(self):
        """Return the name of the sensor."""
        ident = self._device['ident']
        
        result = ident['deviceName']
        if len(result) == 0:
            return ident['type']['value_localized'] + ' ' + _map_key(self._key)
        else:
            return result + ' ' + _map_key(self._key)

    @property
    def state(self):
        """Return the state of the sensor."""

        return self._device['state'][self._key]['value_raw']

    async def async_update(self): 
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.error(' Miele device not found: {}'.format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]

class MieleLocalizedSensor(MieleRawSensor):
    def __init(self, client, device, key):
        pass

    @property
    def state(self):
        """Return the state of the sensor."""
        result = self._device['state']['status']['value_localized']
        if result == None:
            result = self._device['state']['status']['value_raw']

        return result

class MieleTimeSensor(MieleRawSensor):
    def __init(self, hass, device, key):
        pass

    @property
    def state(self):
        """Return the state of the sensor."""
        state_value = self._device['state'][self._key]
        if len(state_value) != 2:
            return None
        else:
            return '{:02d}:{:02d}'.format(state_value[0], state_value[1])

class MieleTemperatureSensor(Entity):

    def __init__(self, hass, device, key, index):
        self._hass = hass
        self._device = device
        self._key = key
        self._index = index

    @property
    def device_id(self):
        """Return the unique ID for this sensor."""
        return self._device['ident']['deviceIdentLabel']['fabNumber']

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self.device_id + '_' + self._key + '_{}'.format(self._index)

    @property
    def name(self):
        """Return the name of the sensor."""
        ident = self._device['ident']
        
        result = ident['deviceName']
        if len(result) == 0:
            return '{} {} {}'.format(ident['type']['value_localized'], _map_key(self._key), self._index)
        else:
            return '{} {} {}'.format(result, _map_key(self._key), self._index)

    @property
    def state(self):
        """Return the state of the sensor."""
        state_value = self._device['state'][self._key][self._index]['value_raw']
        if state_value == -32768:
            return None
        else:
            return state_value / 100

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self._device['state'][self._key][self._index]['unit'] == 'Celsius':
            return "°C"

    @property
    def device_class(self):
        return "temperature"

    async def async_update(self): 
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.error(' Miele device not found: {}'.format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]