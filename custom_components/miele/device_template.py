from typing_extensions import TypedDict
from typing import Any

ValueDict = TypedDict("ValueDict", {"value_raw": int,
                                    "value_localized": str,
                                    "key_localized": str})

RemoteEnable = TypedDict("RemoteEnable", {
    "fullRemoteControl": bool,
    "smartGrid": bool,
    "mobileStart": bool
})

SpinningSpeed = TypedDict("SpinningSpeed", {
    "unit": str,
    "value_raw": Any,
    "value_localized": Any,
    "key_localized": str
})

CurrentWaterConsumption = TypedDict("CurrentWaterConsumption", {
    "unit": str,
    "value": int
})

CurrentEnergyConsumption = TypedDict("CurrentEnergyConsumption", {
    "unit": str,
    "value": float
})

EcoFeedback = TypedDict("EcoFeedback", {
    "currentWaterConsumption": CurrentWaterConsumption,
    "currentEnergyConsumption": CurrentEnergyConsumption,
    "waterForecast": float,
    "energyForecast": float
})

State = TypedDict("State", {
    "ProgramID": ValueDict,
    "status": ValueDict,
    "programType": ValueDict,
    "programPhase": ValueDict,
    "remainingTime": list[int],
    "startTime": list[int],
    "targetTemperature": list[ValueDict],
    "temperature": list[ValueDict],
    "signalInfo": bool,
    "signalFailure": bool,
    "signalDoor": bool,
    "remoteEnable": RemoteEnable,
    "ambientLight": Any,
    "light": Any,
    "elapsedTime": list[int],
    "spinningSpeed": SpinningSpeed,
    "dryingStep": ValueDict,
    "ventilationStep": ValueDict,
    "plateStep": list[ValueDict],
    "ecoFeedback": EcoFeedback,
    "batteryLevel": int
})

DeviceIdentLabel = TypedDict("DeviceIdentLabel", {
    "fabNumber": str,
    "fabIndex": str,
    "techType": str,
    "matNumber": str,
    "swids": list[str]
})

XkmIdentLabel = TypedDict("XkmIdentLabel", {
    "techType": str,
    "releaseVersion": str
})

Ident = TypedDict("Ident", {
    "type": ValueDict,
    "deviceName": str,
    "protocolVersion": int,
    "deviceIdentLabel": DeviceIdentLabel,
    "xkmIdentLabel": XkmIdentLabel
})

Device = TypedDict('Device', {
    "ident": Ident,
    "state": State
})

Result = TypedDict('Result', {
    "state_raw": int,
    "model": str,
    "device_type": str,
    "fabrication_number": str,
    "gateway_type": str,
    "gateway_version": str,

})
