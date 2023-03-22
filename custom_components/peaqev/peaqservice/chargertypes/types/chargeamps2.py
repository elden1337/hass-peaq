from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype_enum import CallTypes

from custom_components.peaqev.peaqservice.chargertypes.const import (
    COMMAND,
    CHARGEPOINT,
    CONNECTOR,
    PARAMETERS,
    CHARGER,
    CHARGERID,
    CURRENT)
from custom_components.peaqev.peaqservice.chargertypes.icharger_type import IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.option_types import OptionTypes
from custom_components.peaqev.peaqservice.chargertypes.models.sensor_types import SensorTypes

SENSORS_SCHEMA = {
    SensorTypes.ChargerEntity: "sensor.{}_1",
    SensorTypes.PowerMeter:    "sensor.{}_1_power",
    SensorTypes.AmpMeter:      "switch.{}_1|max_current",
    SensorTypes.PowerSwitch:   "switch.{}_1"
}

OPTIONS_SCHEMA = {
    OptionTypes.AllowUpdateCurrent:          True,
    OptionTypes.PowerSwitchControlsCharging: True,
    OptionTypes.UpdateCurrentOnTermination:  True
}

CHARGERSTATES_SCHEMA = {
    ChargeControllerStates.Idle:      ["available"],
    ChargeControllerStates.Connected: ["connected"],
    ChargeControllerStates.Charging:  ["charging"]
}

CALLS_SCHEMA = {
    CallTypes.On:
        {
            COMMAND: "enable",
            PARAMETERS: {
                CHARGEPOINT: ">chargerid",
                CONNECTOR:   "chargeamps_connector"
                        }
        },
    CallTypes.Off:
        {
            COMMAND: "disable",
            PARAMETERS: {
                CHARGEPOINT: ">chargerid",
                CONNECTOR:   "chargeamps_connector"
                        }
        },
    CallTypes.UpdateCurrent:
        {
            COMMAND: "set_max_current",
            PARAMETERS: {
                CHARGER:   CHARGEPOINT,
                CHARGERID: ">chargerid",
                CURRENT:   "max_current"
                        }
        }
}

ENTITYENDINGS = ["_power", "_1", "_2", "_status", "_dimmer", "_downlight", "_current", "_voltage"]
NATIVE_CHARGERSTATES = ["available", "connected", "charging"]


class Chargeamps(IChargerType):
    chargeramps_type = ""
    chargeamps_connector: int = 1  # fix this later to be able to use aura

    # def __post_init__(self):
    # return super().__post_init__()
    # self._set_chargeamps_type()

    # def _set_chargeamps_type(self, main_sensor_entity) -> ChargeAmpsTypes:
    # if self._hass.states.get(main_sensor_entity) is not None:
    #     chargeampstype = self._hass.states.get(main_sensor_entity).attributes.get("chargepoint_type")
    #     return ChargeAmpsTypes.get_type(chargeampstype)
