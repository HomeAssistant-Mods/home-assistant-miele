from enum import Enum

from homeassistant.const import STATE_UNKNOWN

from .miele_const import *

TEMP_UNKNOWN = -32768

class DeviceState(Enum):
    """Represents different device states"""    
    UNKNOWN = 0
    OFF = 1
    STAND_BY = 2
    PROGRAMMED = 3
    WAITING_TO_START = 4
    RUNNING = 5
    PAUSED = 6
    END = 7
    FAILURE = 8
    ABORT = 9
    SERVICE = 12
    SUPERFREEZING = 13
    SUPERCOOLING = 14
    LOCKED = 145
    SUPERCOOLING_FREEZING = 146
    NOT_CONNECTED = 255

def convert_time(prop):
    """Converts the given time property into a string representation"""
    if len(prop) == 2:
        return "{:02d}:{:02d}".format(prop[0], prop[1])    
    else:
        return None

def convert_temperature(prop):
    """Remaps the unknown temperature of 32768 to None"""
    if MIELE_ATTRIB_LOCALIZED_VALUE in prop:
        value = prop[MIELE_ATTRIB_LOCALIZED_VALUE] 
        if value == TEMP_UNKNOWN:
            return None
        else:
            return value
    else:
        return None

def localize_value(prop):
    """If a LocalizedValue exists, return it instead of the non-localized variant"""
    if isinstance(prop, (int, bool)):
        return prop
    elif MIELE_ATTRIB_LOCALIZED_VALUE in prop:
        return prop[MIELE_ATTRIB_LOCALIZED_VALUE]
    else:
        do_not_localize(prop)

def do_not_localize(prop):
    """Always return the non-localized variant"""
    if isinstance(prop, (int, bool)):
        return prop
    elif MIELE_ATTRIB_VALUE in prop:
        return prop[MIELE_ATTRIB_VALUE]    
    else:
        return None

def device_state(prop):
    """Converts the device state value to its string representation"""
    if MIELE_ATTRIB_VALUE in prop:
        return DeviceState(prop[MIELE_ATTRIB_VALUE]).name
    else:
        return STATE_UNKNOWN

ATTRIBUTE_CONVERTERS = {
    MIELE_STATE: device_state,

    MIELE_SIGNAL_DOOR: do_not_localize,
    MIELE_SIGNAL_INFO: do_not_localize,
    MIELE_SIGNAL_FAILURE: do_not_localize,

    MIELE_LIGHTING_STATUS: do_not_localize,

    MIELE_DURATION: convert_time,
    MIELE_ELAPSED_TIME: convert_time,
    MIELE_FINISHING_TIME: convert_time,
    MIELE_REMAINING_TIME: convert_time,
    MIELE_START_TIME: convert_time,
        
    MIELE_PLATE_1_ELAPSED_TIME: convert_time,
    MIELE_PLATE_1_REMAINING_TIME: convert_time,
    MIELE_PLATE_2_ELAPSED_TIME: convert_time,
    MIELE_PLATE_2_REMAINING_TIME: convert_time,
    MIELE_PLATE_3_ELAPSED_TIME: convert_time,
    MIELE_PLATE_3_REMAINING_TIME: convert_time,
    MIELE_PLATE_4_ELAPSED_TIME: convert_time,
    MIELE_PLATE_4_REMAINING_TIME: convert_time,
    MIELE_PLATE_5_ELAPSED_TIME: convert_time,
    MIELE_PLATE_5_REMAINING_TIME: convert_time,
    MIELE_PLATE_6_ELAPSED_TIME: convert_time,
    MIELE_PLATE_6_REMAINING_TIME: convert_time,

    MIELE_MEASURED_TEMPERATURE: convert_temperature,
    MIELE_TARGET_TEMPERATURE: convert_temperature,
    MIELE_TEMPERATURE: convert_temperature,
    
    MIELE_PROGRAM_TYPE: do_not_localize,
    MIELE_PROGRAM_ID: localize_value,
    MIELE_PHASE: localize_value,

    MIELE_FRIDGE_STATE: device_state,
    MIELE_FRIDGE_TARGET_TEMPERATURE: convert_temperature,
    MIELE_FRIDGE_CURRENT_TEMPERATURE: convert_temperature,

    MIELE_FREEZER_STATE: device_state,
    MIELE_FREEZER_TARGET_TEMPERATURE: convert_temperature,
    MIELE_FREEZER_CURRENT_TEMPERATURE: convert_temperature,

    MIELE_DEVICE_TEMPERATURE_1: convert_temperature,
    MIELE_DEVICE_TEMPERATURE_2: convert_temperature,

    MIELE_TOP_STATE: device_state,
    MIELE_TOP_TARGET_TEMPERATURE: convert_temperature,
    MIELE_TOP_CURRENT_TEMPERATURE: convert_temperature,

    MIELE_MIDDLE_STATE: device_state,
    MIELE_MIDDLE_TARGET_TEMPERATURE: convert_temperature,
    MIELE_MIDDLE_CURRENT_TEMPERATURE: convert_temperature,

    MIELE_BOTTOM_STATE: device_state,
    MIELE_BOTTOM_TARGET_TEMPERATURE: convert_temperature,
    MIELE_BOTTOM_CURRENT_TEMPERATURE: convert_temperature,
}

def get_converter(key):
    if key in ATTRIBUTE_CONVERTERS:
        return ATTRIBUTE_CONVERTERS[key]
    else:
        return localize_value
