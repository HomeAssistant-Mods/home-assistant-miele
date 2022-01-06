import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import STATE_CLASS_TOTAL_INCREASING, SensorEntity
from homeassistant.const import DEVICE_CLASS_ENERGY
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_registry import async_get_registry

from custom_components.miele import DATA_DEVICES
from custom_components.miele import DOMAIN as MIELE_DOMAIN

PLATFORMS = ["miele"]

_LOGGER = logging.getLogger(__name__)

ALL_DEVICES = []

# https://www.miele.com/developer/swagger-ui/swagger.html#/
STATUS_OFF = 1
STATUS_ON = 2
STATUS_PROGRAMMED = 3
STATUS_PROGRAMMED_WAITING_TO_START = 4
STATUS_RUNNING = 5
STATUS_PAUSE = 6
STATUS_END_PROGRAMMED = 7
STATUS_FAILURE = 8
STATUS_PROGRAMME_INTERRUPTED = 9
STATUS_IDLE = 10
STATUS_RINSE_HOLD = 11
STATUS_SERVICE = 12
STATUS_SUPERFREEZING = 13
STATUS_SUPERCOOLING = 14
STATUS_SUPERHEATING = 15
STATUS_SUPERCOOLING_SUPERFREEZING = 146
STATUS_NOT_CONNECTED = 255


def _map_key(key):
    if key == "status":
        return "Status"
    elif key == "ProgramID":
        return "Program ID"
    elif key == "programType":
        return "Program Type"
    elif key == "programPhase":
        return "Program Phase"
    elif key == "targetTemperature":
        return "Target Temperature"
    elif key == "temperature":
        return "Temperature"
    elif key == "remainingTime":
        return "Remaining Time"
    elif key == "elapsedTime":
        return "Elapsed Time"
    elif key == "startTime":
        return "Start Time"
    elif key == "energyConsumption":
        return "Energy"
    elif key == "waterConsumption":
        return "Water Consumption"


def state_capability(type, state):
    type_str = str(type)
    capabilities = {
        "1": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "targetTemperature",
            "signalInfo",
            "signalFailure",
            "remoteEnable",
            "elapsedTime",
            "spinningSpeed",
            "ecoFeedback",
        ],
        "2": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "signalInfo",
            "signalFailure",
            "remoteEnable",
            "elapsedTime",
            "dryingStep",
            "ecoFeedback",
        ],
        "7": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "signalInfo",
            "signalFailure",
            "remoteEnable",
            "elapsedTime",
            "ecoFeedback",
        ],
        "12": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
            "elapsedTime",
        ],
        "13": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
            "elapsedTime",
        ],
        "14": ["status", "signalFailure", "plateStep"],
        "15": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
            "elapsedTime",
        ],
        "16": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
            "elapsedTime",
        ],
        "17": [
            "ProgramID",
            "status",
            "programPhase",
            "signalInfo",
            "signalFailure",
            "remoteEnable",
        ],
        "18": [
            "status",
            "signalInfo",
            "signalFailure",
            "remoteEnable",
            "ventilationStep",
        ],
        "19": [
            "status",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
        ],
        "20": [
            "status",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
        ],
        "21": [
            "status",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
        ],
        "23": [
            "ProgramID",
            "status",
            "programType",
            "signalInfo",
            "signalFailure",
            "remoteEnable",
            "batteryLevel",
        ],
        "24": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "signalInfo",
            "signalFailure",
            "remoteEnable",
            "elapsedTime",
            "spinningSpeed",
            "dryingStep",
            "ecoFeedback",
        ],
        "25": [
            "status",
            "startTime",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "elapsedTime",
        ],
        "27": ["status", "signalFailure", "plateStep"],
        "31": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
            "elapsedTime",
        ],
        "32": [
            "status",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
        ],
        "33": [
            "status",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
        ],
        "34": [
            "status",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
        ],
        "45": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
            "elapsedTime",
        ],
        "67": [
            "ProgramID",
            "status",
            "programType",
            "programPhase",
            "remainingTime",
            "startTime",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "signalDoor",
            "remoteEnable",
            "elapsedTime",
        ],
        "68": [
            "status",
            "targetTemperature",
            "temperature",
            "signalInfo",
            "signalFailure",
            "remoteEnable",
        ],
    }

    if state in capabilities[type_str]:
        return True


def _is_running(device_status):
    return device_status in [STATUS_RUNNING, STATUS_PAUSE, STATUS_END_PROGRAMMED]


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
        device_state = device["state"]
        device_type = device["ident"]["type"]["value_raw"]

        sensors = []
        if "status" in device_state and state_capability(
            type=device_type, state="status"
        ):
            sensors.append(MieleStatusSensor(hass, device, "status"))

        if "ProgramID" in device_state and state_capability(
            type=device_type, state="ProgramID"
        ):
            sensors.append(MieleTextSensor(hass, device, "ProgramID"))

        if "targetTemperature" in device_state and state_capability(
            type=device_type, state="targetTemperature"
        ):
            for i, val in enumerate(device_state["targetTemperature"]):
                sensors.append(
                    MieleTemperatureSensor(hass, device, "targetTemperature", i)
                )
        if "temperature" in device_state and state_capability(
            type=device_type, state="temperature"
        ):
            for i, val in enumerate(device_state["temperature"]):
                sensors.append(MieleTemperatureSensor(hass, device, "temperature", i))

        if "remainingTime" in device_state and state_capability(
            type=device_type, state="remainingTime"
        ):
            sensors.append(MieleTimeSensor(hass, device, "remainingTime"))
        if "startTime" in device_state and state_capability(
            type=device_type, state="startTime"
        ):
            sensors.append(MieleTimeSensor(hass, device, "startTime"))
        if "elapsedTime" in device_state and state_capability(
            type=device_type, state="elapsedTime"
        ):
            sensors.append(MieleTimeSensor(hass, device, "elapsedTime"))

        if "ecoFeedback" in device_state and state_capability(
            type=device_type, state="ecoFeedback"
        ):
            sensors.append(
                MieleConsumptionSensor(hass, device, "energyConsumption", "kWh")
            )
            sensors.append(
                MieleConsumptionSensor(hass, device, "waterConsumption", "L")
            )

        add_devices(sensors)
        ALL_DEVICES = ALL_DEVICES + sensors


def update_device_state():
    for device in ALL_DEVICES:
        try:
            device.async_schedule_update_ha_state(True)
        except (AssertionError, AttributeError):
            _LOGGER.debug(
                "Component most likely is disabled manually, if not please report to developer"
                "{}".format(device.entity_id)
            )


class MieleRawSensor(Entity):
    def __init__(self, hass, device, key):
        self._hass = hass
        self._device = device
        self._key = key

    @property
    def device_id(self):
        """Return the unique ID for this sensor."""
        return self._device["ident"]["deviceIdentLabel"]["fabNumber"]

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self.device_id + "_" + self._key

    @property
    def name(self):
        """Return the name of the sensor."""
        ident = self._device["ident"]

        result = ident["deviceName"]
        if len(result) == 0:
            return ident["type"]["value_localized"] + " " + _map_key(self._key)
        else:
            return result + " " + _map_key(self._key)

    @property
    def state(self):
        """Return the state of the sensor."""

        return self._device["state"][self._key]["value_raw"]

    async def async_update(self):
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.debug("Miele device disappeared: {}".format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]


class MieleSensorEntity(SensorEntity):
    def __init__(self, hass, device, key):
        self._hass = hass
        self._device = device
        self._key = key

    @property
    def device_id(self):
        """Return the unique ID for this sensor."""
        return self._device["ident"]["deviceIdentLabel"]["fabNumber"]

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self.device_id + "_" + self._key

    @property
    def name(self):
        """Return the name of the sensor."""
        ident = self._device["ident"]

        result = ident["deviceName"]
        if len(result) == 0:
            return ident["type"]["value_localized"] + " " + _map_key(self._key)
        else:
            return result + " " + _map_key(self._key)

    async def async_update(self):
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.debug("Miele device disappeared: {}".format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]


class MieleStatusSensor(MieleRawSensor):
    @property
    def state(self):
        """Return the state of the sensor."""
        result = self._device["state"]["status"]["value_localized"]
        if result == None:
            result = self._device["state"]["status"]["value_raw"]

        return result

    @property
    def extra_state_attributes(self):
        """Attributes."""
        device_state = self._device["state"]

        attributes = {}
        if "ProgramID" in device_state:
            attributes["ProgramID"] = device_state["ProgramID"]["value_localized"]
            attributes["rawProgramID"] = device_state["ProgramID"]["value_raw"]

        if "programType" in device_state:
            attributes["programType"] = device_state["programType"]["value_localized"]
            attributes["rawProgramType"] = device_state["programType"]["value_raw"]

        if "programPhase" in device_state:
            attributes["programPhase"] = device_state["programPhase"]["value_localized"]
            attributes["rawProgramPhase"] = device_state["programPhase"]["value_raw"]

        if "dryingStep" in device_state:
            attributes["dryingStep"] = device_state["dryingStep"]["value_localized"]
            attributes["rawDryingStep"] = device_state["dryingStep"]["value_raw"]

        if "spinningSpeed" in device_state:
            attributes["spinningSpeed"] = device_state["spinningSpeed"][
                "value_localized"
            ]
            attributes["rawSpinningSpeed"] = device_state["spinningSpeed"]["value_raw"]

        if "ventilationStep" in device_state:
            attributes["ventilationStep"] = device_state["ventilationStep"][
                "value_localized"
            ]
            attributes["rawVentilationStep"] = device_state["ventilationStep"][
                "value_raw"
            ]

        if "plateStep" in device_state:
            plate_steps = 1
            for plateStep in device_state["plateStep"]:
                attributes["plateStep" + str(plate_steps)] = plateStep[
                    "value_localized"
                ]
                attributes["rawPlateStep" + str(plate_steps)] = plateStep["value_raw"]
                plate_steps += 1

        if "ecoFeedback" in device_state and device_state["ecoFeedback"] is not None:
            if "currentWaterConsumption" in device_state["ecoFeedback"]:
                attributes["currentWaterConsumption"] = device_state["ecoFeedback"][
                    "currentWaterConsumption"
                ]["value"]
                attributes["currentWaterConsumptionUnit"] = device_state["ecoFeedback"][
                    "currentWaterConsumption"
                ]["unit"]
            if "currentEnergyConsumption" in device_state["ecoFeedback"]:
                attributes["currentEnergyConsumption"] = device_state["ecoFeedback"][
                    "currentEnergyConsumption"
                ]["value"]
                attributes["currentEnergyConsumptionUnit"] = device_state[
                    "ecoFeedback"
                ]["currentEnergyConsumption"]["unit"]
            if "waterForecast" in device_state["ecoFeedback"]:
                attributes["waterForecast"] = device_state["ecoFeedback"][
                    "waterForecast"
                ]
            if "energyForecast" in device_state["ecoFeedback"]:
                attributes["energyForecast"] = device_state["ecoFeedback"][
                    "energyForecast"
                ]

        # Programs will only be running of both remainingTime and elapsedTime indicate
        # a value > 0
        if "remainingTime" in device_state and "elapsedTime" in device_state:
            remainingTime = _to_seconds(device_state["remainingTime"])
            elapsedTime = _to_seconds(device_state["elapsedTime"])

            if "startTime" in device_state:
                startTime = _to_seconds(device_state["startTime"])
            else:
                startTime = 0

            # Calculate progress
            if (elapsedTime + remainingTime) == 0:
                attributes["progress"] = None
            else:
                attributes["progress"] = round(
                    elapsedTime / (elapsedTime + remainingTime) * 100, 1
                )

            # Calculate end time
            if remainingTime == 0:
                attributes["finishTime"] = None
            else:
                now = datetime.now()
                attributes["finishTime"] = (
                    now
                    + timedelta(seconds=startTime)
                    + timedelta(seconds=remainingTime)
                ).strftime("%H:%M")

            # Calculate start time
            if startTime == 0:
                now = datetime.now()
                attributes["kickoffTime"] = (
                    now - timedelta(seconds=elapsedTime)
                ).strftime("%H:%M")
            else:
                now = datetime.now()
                attributes["kickoffTime"] = (
                    now + timedelta(seconds=startTime)
                ).strftime("%H:%M")

        return attributes


class MieleConsumptionSensor(MieleSensorEntity):
    def __init__(self, hass, device, key, measurement):
        super().__init__(hass, device, key)

        self._attr_native_unit_of_measurement = measurement
        self._cached_consumption = -1
        self._attr_state_class = STATE_CLASS_TOTAL_INCREASING

        if key == "energyConsumption":
            self._attr_device_class = DEVICE_CLASS_ENERGY

    @property
    def state(self):
        """Return the state of the sensor."""
        device_state = self._device["state"]
        device_status_value = self._device["state"]["status"]["value_raw"]

        if not _is_running(device_status_value):
            self._cached_consumption = -1
            return 0

        if self._cached_consumption >= 0:
            if (
                "ecoFeedback" not in device_state
                or device_state["ecoFeedback"] is None
                or device_status_value == STATUS_NOT_CONNECTED
            ):
                return self._cached_consumption

        consumption = 0
        if self._key == "energyConsumption":
            if "currentEnergyConsumption" in device_state["ecoFeedback"]:
                consumption_container = device_state["ecoFeedback"][
                    "currentEnergyConsumption"
                ]

                if consumption_container["unit"] == "kWh":
                    consumption = consumption_container["value"]
                elif consumption_container["unit"] == "Wh":
                    consumption = consumption_container["value"] / 1000.0
            else:
                return self._cached_consumption

        elif self._key == "waterConsumption":
            if "currentWaterConsumption" in device_state["ecoFeedback"]:
                consumption = device_state["ecoFeedback"]["currentWaterConsumption"][
                    "value"
                ]
            else:
                return self._cached_consumption

        self._cached_consumption = consumption
        return consumption


class MieleTimeSensor(MieleRawSensor):
    @property
    def state(self):
        """Return the state of the sensor."""
        state_value = self._device["state"][self._key]
        if len(state_value) != 2:
            return None
        else:
            return "{:02d}:{:02d}".format(state_value[0], state_value[1])


class MieleTemperatureSensor(Entity):
    def __init__(self, hass, device, key, index):
        self._hass = hass
        self._device = device
        self._key = key
        self._index = index

    @property
    def device_id(self):
        """Return the unique ID for this sensor."""
        return self._device["ident"]["deviceIdentLabel"]["fabNumber"]

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self.device_id + "_" + self._key + "_{}".format(self._index)

    @property
    def name(self):
        """Return the name of the sensor."""
        ident = self._device["ident"]

        result = ident["deviceName"]
        if len(result) == 0:
            return "{} {} {}".format(
                ident["type"]["value_localized"], _map_key(self._key), self._index
            )
        else:
            return "{} {} {}".format(result, _map_key(self._key), self._index)

    @property
    def state(self):
        """Return the state of the sensor."""
        state_value = self._device["state"][self._key][self._index]["value_raw"]
        if state_value == -32768:
            return None
        else:
            return state_value / 100

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self._device["state"][self._key][self._index]["unit"] == "Celsius":
            return "°C"
        elif self._device["state"][self._key][self._index]["unit"] == "Fahrenheit":
            return "°F"

    @property
    def device_class(self):
        return "temperature"

    async def async_update(self):
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.debug(" Miele device disappeared: {}".format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]


class MieleTextSensor(MieleRawSensor):
    @property
    def state(self):
        """Return the state of the sensor."""
        result = self._device["state"][self._key]["value_localized"]
        if result == "":
            result = None

        return result
