import logging

from datetime import timedelta, datetime

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

def _to_seconds(time_array):
    if len(time_array) == 3:
        return time_array[0] * 3600 + time_array[1] * 60 + time_array[2]
    elif len(time_array) == 2:
        return time_array[0] * 3600 + time_array[1] * 60
    else:
        return 0

# pylint: disable=W0612
def setup_platform(hass, config, add_devices, discovery_info=None):
    global ALL_DEVICES
    
    devices = hass.data[MIELE_DOMAIN][DATA_DEVICES]
    for k, device in devices.items():
        device_state = device['state']

        sensors = []
        if 'status' in device_state:
            sensors.append(MieleStatusSensor(hass, device, 'status'))

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
            _LOGGER.error('Miele device disappeared: {}'.format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]

class MieleStatusSensor(MieleRawSensor):
    def __init(self, client, device, key):
        pass

    @property
    def state(self):
        """Return the state of the sensor."""
        result = self._device['state']['status']['value_localized']
        if result == None:
            result = self._device['state']['status']['value_raw']

        return result

    @property
    def device_state_attributes(self):
        """Attributes."""
        device_state = self._device['state']

        attributes = {}
        if 'programType' in device_state:
            attributes['programType'] = device_state['programType']['value_localized']
            attributes['rawProgramType'] = device_state['programType']['value_raw']

        if 'programPhase' in device_state:
            attributes['programPhase'] = device_state['programPhase']['value_localized']
            attributes['rawProgramPhase'] = device_state['programPhase']['value_raw']

        if 'dryingStep' in device_state:
            attributes['dryingStep'] = device_state['dryingStep']['value_localized']
            attributes['rawDryingStep'] = device_state['dryingStep']['value_raw']

        if 'ventilationStep' in device_state:
            attributes['ventilationStep'] = device_state['ventilationStep']['value_localized']
            attributes['rawVentilationStep'] = device_state['ventilationStep']['value_raw']

        # Programs will only be running of both remainingTime and elapsedTime indicate 
        # a value > 0
        if 'remainingTime' in device_state and 'elapsedTime' in device_state:
            remainingTime = _to_seconds(device_state['remainingTime'])
            elapsedTime = _to_seconds(device_state['elapsedTime'])

            # Calculate progress            
            if (elapsedTime + remainingTime) == 0:
                attributes['progress'] = None
            else:
                attributes['progress'] = round(elapsedTime / (elapsedTime + remainingTime) * 100, 1)

            # Calculate end time
            if remainingTime == 0:
                attributes['finishTime'] = None
            else:
                now = datetime.now()
                attributes['finishTime'] = (now + timedelta(seconds=remainingTime)).strftime('%H:%M')

        return attributes


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
        elif self._device['state'][self._key][self._index]['unit'] == 'Fahrenheit':
            return "°F"

    @property
    def device_class(self):
        return "temperature"

    async def async_update(self): 
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.error(' Miele device disappeared: {}'.format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]
