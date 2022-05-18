import logging

from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from peaqevcore.Models import CHARGERSTATES
from custom_components.peaqev.peaqservice.chargertypes.calltype import CallType
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = [
    "_power",
    "_status",
    "_dimmer",
    "_downlight",
    "_lifetime_energy",
    "_online",
    "_current",
    "_voltage",
    "_output_limit",
    "_cost_per_kwh",
    "_enable_idle_current"
]

DOMAINNAME = "easee"
UPDATECURRENT = True
#docs: https://github.com/fondberg/easee_hass

"""
UNUSED STATES FROM EASEE

completed
error
"""

class Easee(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid, auth_required: bool = False):
        super().__init__(hass)
        self._chargerid = chargerid
        self.getentities(DOMAINNAME, ENTITYENDINGS)
        self._chargerstates[CHARGERSTATES.Idle] = ["disconnected"]
        self._chargerstates[CHARGERSTATES.Connected] = ["awaiting_start", "ready_to_charge"]
        self._chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self._chargerstates[CHARGERSTATES.Done] = ["completed"]
        self.chargerentity = f"sensor.{self._entityschema}_status"
        self.powermeter = f"sensor.{self._entityschema}_power"
        self.powermeter_factor = 1000
        self.powerswitch = f"switch.{self._entityschema}_is_enabled"
        self.ampmeter = f"sensor.{self._entityschema}_max_charger_limit"
        self.ampmeter_is_attribute = False
        self._auth_required = auth_required

        servicecall_params = {
            CHARGER: "charger_id",
            CHARGERID: self._chargerid,
            CURRENT: "current"
        }

        _on_off_params = {"charger_id": self._chargerid}
        _on_params = {}
        _off_params = {}

        _on = CallType("start", _on_off_params)
        _off = CallType("stop", _on_off_params)
        _resume = CallType("set_charger_dynamic_limit", {"mode": "6", "charger_id": self._chargerid})
        _pause = CallType("set_charger_dynamic_limit", {"mode": "0", "charger_id": self._chargerid})

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call=_on if self._auth_required is True else _resume,
            off_call=_off if self._auth_required is True else _pause,
            pause_call=_pause,
            resume_call=_resume,
            allowupdatecurrent=UPDATECURRENT,
            update_current_call="set_charger_dynamic_limit",
            update_current_params=servicecall_params
        )
