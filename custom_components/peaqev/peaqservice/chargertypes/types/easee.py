import logging

from homeassistant.core import HomeAssistant
from peaqevcore.Models import CHARGERSTATES

from custom_components.peaqev.peaqservice.chargertypes.calltype import CallType
from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = [
    "_dimmer",
    "_downlight",
    "_current",
    "_voltage",
    "_output_limit",
    "_cost_per_kwh",
    "_enable_idle_current",
    "_is_enabled",
    "_cable_locked_permanently",
    "_smart_charging",
    "_max_charger_limit",
    "_energy_per_hour",
    "_lifetime_energy",
    "_session_energy",
    "_power",
    "_status",
    "_online",
    "_cable_locked"
]

NATIVE_CHARGERSTATES = [
    "disconnected",
    "awaiting_start",
    "charging",
    "ready_to_charge",
    "completed",
    "error"
]

DOMAINNAME = "easee"
UPDATECURRENT = True
UPDATECURRENT_ON_TERMINATION = False
#docs: https://github.com/fondberg/easee_hass


class Easee(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid, auth_required: bool = False):
        super().__init__(hass)
        self._chargerid = chargerid
        self._auth_required = auth_required
        self._domainname = DOMAINNAME
        self._entityendings = ENTITYENDINGS
        self._native_chargerstates = NATIVE_CHARGERSTATES
        self._chargerstates[CHARGERSTATES.Idle] = ["disconnected"]
        self._chargerstates[CHARGERSTATES.Connected] = ["awaiting_start", "ready_to_charge"]
        self._chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self._chargerstates[CHARGERSTATES.Done] = ["completed"]
        self.getentities()
        self.set_sensors()

        servicecall_params = {
            CHARGER: "charger_id",
            CHARGERID: self._chargerid,
            CURRENT: "current"
        }

        _on_off_params = {"charger_id": self._chargerid}

        _on = CallType("start", _on_off_params)
        _off = CallType("stop", _on_off_params)
        _resume = CallType("set_charger_dynamic_limit", {"current": "6", "charger_id": self._chargerid})
        _pause = CallType("set_charger_dynamic_limit", {"current": "0", "charger_id": self._chargerid})

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call=_on if self._auth_required is True else _resume,
            off_call=_off if self._auth_required is True else _pause,
            pause_call=_pause,
            resume_call=_resume,
            allowupdatecurrent=UPDATECURRENT,
            update_current_call="set_charger_dynamic_limit",
            update_current_params=servicecall_params,
            update_current_on_termination = UPDATECURRENT_ON_TERMINATION
        )

    def set_sensors(self):
        amp_sensor = f"sensor.{self._entityschema}_dynamic_charger_limit"
        if not self._validate_sensor(amp_sensor):
            amp_sensor = f"sensor.{self._entityschema}_max_charger_limit"

        self.chargerentity = f"sensor.{self._entityschema}_status"
        self.powermeter = f"sensor.{self._entityschema}_power"
        self.powermeter_factor = 1000
        self.powerswitch = f"switch.{self._entityschema}_is_enabled"
        self.ampmeter = amp_sensor
        self.ampmeter_is_attribute = False

    def _validate_sensor(self, sensor:str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        elif ret.state == "Null":
            return False
        return True