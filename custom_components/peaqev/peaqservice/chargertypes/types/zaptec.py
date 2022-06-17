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

#ENTITYENDINGS = []

NATIVE_CHARGERSTATES = [
"unknown",
"charging",
"disconnected",
"waiting",
"charge_done"
]

DOMAINNAME = "zaptec"
UPDATECURRENT = False
UPDATECURRENT_ON_TERMINATION = False
#docs: https://github.com/custom-components/zaptec


class Zaptec(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid, auth_required: bool = False):
        super().__init__(hass)
        self._chargerid = chargerid
        self._auth_required = auth_required
        self._powerswitch_controls_charging = False
        self._domainname = DOMAINNAME
        self._native_chargerstates = NATIVE_CHARGERSTATES
        self._chargerstates[CHARGERSTATES.Idle] = ["disconnected"]
        self._chargerstates[CHARGERSTATES.Connected] = ["waiting"]
        self._chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self._chargerstates[CHARGERSTATES.Done] = ["charge_done"]
        self.getentities()
        self.set_sensors()

        # servicecall_params = {
        #     CHARGER: "charger_id",
        #     CHARGERID: self._chargerid,
        #     CURRENT: "current"
        # }

        _on_off_params = {"charger_id": self._chargerid}

        _on = CallType("start_charging", _on_off_params)
        _off = CallType("stop_charging", _on_off_params)
        _resume = CallType("resume_charging", _on_off_params)
        _pause = CallType("stop_pause_charging", _on_off_params)

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call=_on,
            off_call=_off,
            pause_call=_pause,
            resume_call=_resume,
            allowupdatecurrent=UPDATECURRENT
        )

    def set_sensors(self):
        self.chargerentity = f"sensor.zaptec_{self._entityschema}"
        self.powermeter = "total_charge_power" #attribute on chargerentity
        self.powermeter_is_attribute = True
        self.powermeter_factor = 1
        self.powerswitch = f"switch.zaptec_{self._entityschema}_switch"

    def _validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        elif ret.state == "Null":
            return False
        return True
