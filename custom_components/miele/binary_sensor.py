import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import Entity

from custom_components.miele import CAPABILITIES, DATA_DEVICES
from custom_components.miele import DOMAIN as MIELE_DOMAIN

PLATFORMS = ["miele"]

_LOGGER = logging.getLogger(__name__)

ALL_DEVICES = []


def state_capability(type, state):
    type_str = str(type)
    if state in CAPABILITIES[type_str]:
        return True


def _map_key(key):
    if key == "signalInfo":
        return "Info"
    elif key == "signalFailure":
        return "Failure"
    elif key == "signalDoor":
        return "Door"
    elif key == "mobileStart":
        return "MobileStart"


# pylint: disable=W0612
def setup_platform(hass, config, add_devices, discovery_info=None):
    global ALL_DEVICES

    devices = hass.data[MIELE_DOMAIN][DATA_DEVICES]
    for k, device in devices.items():
        device_state = device["state"]
        device_type = device["ident"]["type"]["value_raw"]

        binary_devices = []
        if "signalInfo" in device_state and state_capability(
            type=device_type, state="signalInfo"
        ):
            binary_devices.append(MieleBinarySensor(hass, device, "signalInfo"))
        if "signalFailure" in device_state and state_capability(
            type=device_type, state="signalFailure"
        ):
            binary_devices.append(MieleBinarySensor(hass, device, "signalFailure"))
        if "signalDoor" in device_state and state_capability(
            type=device_type, state="signalDoor"
        ):
            binary_devices.append(MieleBinarySensor(hass, device, "signalDoor"))
        if "remoteEnable" in device_state and state_capability(
            type=device_type, state="remoteEnable"
        ):
            remote_state = device_state["remoteEnable"]
            if "mobileStart" in remote_state:
                binary_devices.append(
                    MieleBinarySensor(hass, device, "remoteEnable.mobileStart")
                )

        add_devices(binary_devices)
        ALL_DEVICES = ALL_DEVICES + binary_devices


def update_device_state():
    for device in ALL_DEVICES:
        try:
            device.async_schedule_update_ha_state(True)
        except (AssertionError, AttributeError):
            _LOGGER.debug(
                "Component most likely is disabled manually, if not please report to developer"
                "{}".format(device.entity_id)
            )


class MieleBinarySensor(BinarySensorEntity):
    def __init__(self, hass, device, key):
        self._hass = hass
        self._device = device
        self._keys = key.split(".")
        self._key = self._keys[-1]
        self._ha_key = _map_key(self._key)

    @property
    def device_id(self):
        """Return the unique ID for this sensor."""
        return self._device["ident"]["deviceIdentLabel"]["fabNumber"]

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self.device_id + "_" + self._ha_key

    @property
    def name(self):
        """Return the name of the sensor."""
        ident = self._device["ident"]

        result = ident["deviceName"]
        if len(result) == 0:
            return ident["type"]["value_localized"] + " " + self._ha_key
        else:
            return result + " " + self._ha_key

    @property
    def is_on(self):
        """Return the state of the sensor."""
        current_val = self._device["state"]
        for k in self._keys:
            current_val = current_val[k]
        return bool(current_val)

    @property
    def device_class(self):
        if self._key == "signalDoor":
            return "door"
        elif self._key == "mobileStart":
            return "running"
        else:
            return "problem"

    async def async_update(self):
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.debug("Miele device not found: {}".format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]
