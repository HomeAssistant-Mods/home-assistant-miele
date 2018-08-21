import logging

from datetime import timedelta

from homeassistant.helpers.entity import Entity

from custom_components.miele import DOMAIN as MIELE_DOMAIN, DATA_CLIENT

PLATFORMS = ['miele']

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)

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
    client = hass.data[MIELE_DOMAIN][DATA_CLIENT]
    devices = client.get_devices()

    for device in devices:
        device_state = device['state']

        sensors = []
        if 'status' in device_state:
            sensors.append(MieleLocalizedSensor(client, device, 'status'))

        if 'programType' in device_state:
            sensors.append(MieleRawSensor(client, device, 'programType'))
        if 'programPhase' in device_state:
            sensors.append(MieleRawSensor(client, device, 'programPhase'))

        if 'targetTemperature' in device_state:
            for i, val in enumerate(device_state['targetTemperature']):
                sensors.append(MieleTemperatureSensor(client, device, 'targetTemperature', i))
        if 'temperature' in device_state:
            for i, val in enumerate(device_state['temperature']):
                sensors.append(MieleTemperatureSensor(client, device, 'temperature', i))

        if 'remainingTime' in device_state:
            sensors.append(MieleTimeSensor(client, device, 'remainingTime'))
        if 'startTime' in device_state:
            sensors.append(MieleTimeSensor(client, device, 'startTime'))
        if 'elapsedTime' in device_state:
            sensors.append(MieleTimeSensor(client, device, 'elapsedTime'))


        add_devices(sensors)

class MieleRawSensor(Entity):

    def __init__(self, client, device, key):
        self._client = client
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

    def update(self): 
        # _LOGGER.info(f'Updating Miele Binary Sensor {self.unique_id}')
        self._device = self._client.get_device(self.device_id)
        return

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
    def __init(self, client, device, key):
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

    def __init__(self, client, device, key, index):
        self._client = client
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

    def update(self): 
        # _LOGGER.info(f'Updating Miele Binary Sensor {self.unique_id}')
        self._device = self._client.get_device(self.device_id)
        return