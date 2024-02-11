"""Support for the Miele Sensors."""

import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CAPABILITIES
from .coordinator import MieleDataUpdateCoordinator
from .entity import MieleEntity

_LOGGER = logging.getLogger(__name__)

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
    elif key == "dryingStep":
        return "Drying Step"
    elif key == "spinningSpeed":
        return "Spin Speed"
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
    elif key == "batteryLevel":
        return "Battery Level"
    elif key == "energyForecast":
        return "Energy cons. forecast"
    elif key == "waterForecast":
        return "Water cons. forecast"


def state_capability(type, state) -> bool:
    """Check the capabilities."""
    type_str = str(type)
    if state in CAPABILITIES[type_str]:
        return True


def _is_running(device_status):
    return device_status in [
        STATUS_RUNNING,
        STATUS_PAUSE,
        STATUS_END_PROGRAMMED,
        STATUS_PROGRAMME_INTERRUPTED,
        STATUS_RINSE_HOLD,
    ]


def _is_terminated(device_status):
    return device_status in [STATUS_END_PROGRAMMED, STATUS_PROGRAMME_INTERRUPTED]


def _to_seconds(time_array):
    if len(time_array) == 3:
        return time_array[0] * 3600 + time_array[1] * 60 + time_array[2]
    elif len(time_array) == 2:
        return time_array[0] * 3600 + time_array[1] * 60
    else:
        return 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Load Sensors from the config settings."""
    coordinator: MieleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    devices = coordinator.data
    for _, device in devices.items():
        device_state = device["state"]
        device_type = device["ident"]["type"]["value_raw"]

        if "status" in device_state and state_capability(
            type=device_type, state="status"
        ):
            entities.append(MieleStatusSensor(coordinator, device, "status"))

        if "ProgramID" in device_state and state_capability(
            type=device_type, state="ProgramID"
        ):
            entities.append(MieleTextSensor(coordinator, device, "ProgramID"))

        if "programPhase" in device_state and state_capability(
            type=device_type, state="programPhase"
        ):
            entities.append(MieleTextSensor(coordinator, device, "programPhase"))

        if "targetTemperature" in device_state and state_capability(
            type=device_type, state="targetTemperature"
        ):
            for i, _ in enumerate(device_state["targetTemperature"]):
                entities.append(
                    MieleTemperatureSensor(coordinator, device, "targetTemperature", i)
                )

        # washer, washer-dryer and dishwasher only have first target temperarure sensor
        if "targetTemperature" in device_state and state_capability(
            type=device_type, state="targetTemperature.0"
        ):
            entities.append(
                MieleTemperatureSensor(
                    coordinator, device, "targetTemperature", 0, True
                )
            )

        if "temperature" in device_state and state_capability(
            type=device_type, state="temperature"
        ):
            for i, _ in enumerate(device_state["temperature"]):
                entities.append(
                    MieleTemperatureSensor(coordinator, device, "temperature", i)
                )

        if "dryingStep" in device_state and state_capability(
            type=device_type, state="dryingStep"
        ):
            entities.append(MieleTextSensor(coordinator, device, "dryingStep"))

        if "spinningSpeed" in device_state and state_capability(
            type=device_type, state="spinningSpeed"
        ):
            entities.append(MieleTextSensor(coordinator, device, "spinningSpeed"))

        if "remainingTime" in device_state and state_capability(
            type=device_type, state="remainingTime"
        ):
            entities.append(MieleTimeSensor(coordinator, device, "remainingTime", True))
        if "startTime" in device_state and state_capability(
            type=device_type, state="startTime"
        ):
            entities.append(MieleTimeSensor(coordinator, device, "startTime"))
        if "elapsedTime" in device_state and state_capability(
            type=device_type, state="elapsedTime"
        ):
            entities.append(MieleTimeSensor(coordinator, device, "elapsedTime"))

        if "ecoFeedback" in device_state and state_capability(
            type=device_type, state="ecoFeedback.energyConsumption"
        ):
            entities.append(
                MieleConsumptionSensor(
                    coordinator,
                    device,
                    "energyConsumption",
                    "kWh",
                    SensorDeviceClass.ENERGY,
                )
            )

        if "ecoFeedback" in device_state and state_capability(
            type=device_type, state="ecoFeedback.waterConsumption"
        ):
            entities.append(
                MieleConsumptionForecastSensor(coordinator, device, "energyForecast")
            )

        if "ecoFeedback" in device_state and state_capability(
            type=device_type, state="ecoFeedback.waterConsumption"
        ):
            entities.append(
                MieleConsumptionSensor(
                    coordinator, device, "waterConsumption", "L", None
                )
            )
            entities.append(
                MieleConsumptionForecastSensor(coordinator, device, "waterForecast")
            )

        if "batteryLevel" in device_state and state_capability(
            type=device_type, state="batteryLevel"
        ):
            entities.append(MieleBatterySensor(coordinator, device, "batteryLevel"))

    async_add_entities(entities, True)
    coordinator.remove_old_entities(Platform.SENSOR)


class MieleStatusSensor(MieleEntity):
    """Miele Status Raw Entity."""

    def __init__(
        self,
        coordinator: MieleDataUpdateCoordinator,
        device: dict[str, any],
        key: str,
    ):
        """Initialise Miele Raw Sensor."""
        self._key = key
        super().__init__(coordinator, Platform.SENSOR, device, key, _map_key(key))

    @property
    def state(self):
        """Return the state of the sensor."""
        result = self.device["state"]["status"]["value_localized"]
        if result is None:
            result = self.device["state"]["status"]["value_raw"]

        return result

    @property
    def extra_state_attributes(self):
        """Attributes."""
        device_state = self.device["state"]

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


class MieleConsumptionSensor(MieleEntity, SensorEntity):
    """Consumption Sensor."""

    def __init__(self, coordinator, device, key, measurement, device_class):
        """Initialize the Class."""
        super().__init__(coordinator, Platform.SENSOR, device, key, _map_key(key))

        self._attr_native_unit_of_measurement = measurement
        self._cached_consumption = -1
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_device_class = device_class

    @property
    def state(self):
        """Return the state of the sensor."""
        device_state = self.device["state"]
        device_status_value = self.device["state"]["status"]["value_raw"]

        if (
            not _is_running(device_status_value)
            and device_status_value != STATUS_NOT_CONNECTED
        ):
            self._cached_consumption = -1
            return 0

        if self._cached_consumption >= 0:
            if (
                "ecoFeedback" not in device_state
                or device_state["ecoFeedback"] is None
                or device_status_value == STATUS_NOT_CONNECTED
            ):
                # Sometimes the Miele API seems to return a null ecoFeedback
                # object even though the Miele device is running. Or if the the
                # Miele device has lost the connection to the Miele cloud, the
                # status is "not connected". Either way, we need to return the
                # last known value until the API starts returning something
                # sane again, otherwise the statistics generated from this
                # sensor would be messed up.
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


class MieleTimeSensor(MieleEntity):
    """Time Raw for Running Times."""

    def __init__(
        self,
        coordinator: MieleDataUpdateCoordinator,
        device: dict[str, any],
        key: str,
        decreasing=False,
    ):
        """Initialise Miele Raw Sensor."""
        super().__init__(coordinator, Platform.SENSOR, device, key, _map_key(key))
        self._key = key
        self._init_value = "--:--"
        self._cached_time = self._init_value
        self._decreasing = decreasing

    @property
    def state(self):
        """Return the state of the sensor."""
        state_value = self.device["state"][self._key]
        device_status_value = self.device["state"]["status"]["value_raw"]
        formatted_value = None
        if len(state_value) == 2:
            formatted_value = f"{state_value[0]:02d}:{state_value[1]:02d}"

        if (
            not _is_running(device_status_value)
            and device_status_value != STATUS_NOT_CONNECTED
        ):
            self._cached_time = self._init_value
            return formatted_value

        if self._cached_time != self._init_value:
            # As for energy consumption, also this information could become "00:00"
            # when appliance is not reachable. Provide cached value in that case.
            # Some appliances also clear time status when terminating program.
            if self._decreasing and _is_terminated(device_status_value):
                return formatted_value
            elif (
                formatted_value is None
                or device_status_value == STATUS_NOT_CONNECTED
                or _is_terminated(device_status_value)
            ):
                return self._cached_time

        self._cached_time = formatted_value
        return formatted_value


class MieleTemperatureSensor(MieleEntity):
    """Temperature Sensor."""

    def __init__(self, coordinator, device, key, index, force_int=False):
        """Initialize the Class."""
        super().__init__(
            coordinator, Platform.SENSOR, device, key, f"{_map_key(key)} {index}"
        )
        self._index = index
        self._force_int = force_int

    @property
    def state(self):
        """Return the state of the sensor."""
        state_value = self.device["state"][self._key][self._index]["value_raw"]
        if state_value == -32768:
            return None
        elif self._force_int:
            return int(state_value / 100)
        else:
            return state_value / 100

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self.device["state"][self._key][self._index]["unit"] == "Celsius":
            return "°C"
        elif self.device["state"][self._key][self._index]["unit"] == "Fahrenheit":
            return "°F"

    @property
    def device_class(self):
        """Return the Class of the Sensor."""
        return "temperature"


class MieleTextSensor(MieleEntity):
    """General Text Raw Entity."""

    def __init__(
        self,
        coordinator: MieleDataUpdateCoordinator,
        device: dict[str, any],
        key: str,
    ):
        """Initialise Miele Raw Sensor."""
        super().__init__(coordinator, Platform.SENSOR, device, key, _map_key(key))

    @property
    def state(self):
        """Return the state of the sensor."""
        result = self.device["state"][self._key]["value_localized"]
        if result == "":
            result = None

        return result


class MieleBatterySensor(MieleEntity, SensorEntity):
    """Sensor for Batteries."""

    def __init__(self, coordinator, device, key):
        """Initialize the Class."""
        super().__init__(coordinator, Platform.SENSOR, device, key, _map_key(key))

        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self):
        """Return Sensor State."""
        return self.device["state"][self._key]


class MieleConsumptionForecastSensor(MieleEntity, SensorEntity):
    """Forecast Consumption Sensor."""

    def __init__(self, coordinator, device, key):
        """Initizlise Class."""
        super().__init__(coordinator, Platform.SENSOR, device, key, _map_key(key))

        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self):
        """Return the state of the sensor."""
        device_state = self.device["state"]

        if (
            device_state["ecoFeedback"] is not None
            and self._key in device_state["ecoFeedback"]
        ):
            return device_state["ecoFeedback"][self._key] * 100

        return None
