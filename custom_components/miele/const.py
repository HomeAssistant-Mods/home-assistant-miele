"""Miele Constants."""

from homeassistant.const import Platform

DOMAIN = "miele"
VERSION = "v2024.2.13-b0"

DEFAULT_SCAN_INTERVAL = 5

OAUTH_AUTHORIZE_URL = "https://api.mcs3.miele.com/thirdparty/login"
OAUTH_TOKEN_URL = "https://api.mcs3.miele.com/thirdparty/token"

ENTITIES = [
    Platform.BINARY_SENSOR,
    Platform.FAN,
    Platform.LIGHT,
    Platform.SENSOR,
]

CAPABILITIES = {
    "1": [
        "ProgramID",
        "status",
        "programType",
        "programPhase",
        "remainingTime",
        "startTime",
        "targetTemperature.0",
        "signalInfo",
        "signalFailure",
        "signalDoor",
        "remoteEnable",
        "elapsedTime",
        "spinningSpeed",
        "ecoFeedback.energyConsumption",
        "ecoFeedback.waterConsumption",
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
        "signalDoor",
        "remoteEnable",
        "elapsedTime",
        "dryingStep",
        "ecoFeedback.energyConsumption",
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
        "ecoFeedback.energyConsumption",
        "ecoFeedback.waterConsumption",
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
        "targetTemperature.0",
        "startTime",
        "signalInfo",
        "signalFailure",
        "signalDoor",
        "remoteEnable",
        "elapsedTime",
        "spinningSpeed",
        "dryingStep",
        "ecoFeedback.energyConsumption",
        "ecoFeedback.waterConsumption",
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
