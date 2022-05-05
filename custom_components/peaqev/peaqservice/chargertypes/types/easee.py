import logging

from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from peaqevcore.Models import CHARGERSTATES
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = ["_power", "_status", "_dimmer", "_downlight", "_lifetime_energy", "_online", "_current", "_voltage", "_output_limit", "_cost_per_kwh", "_enable_idle_current"]
DOMAINNAME = "easee"
UPDATECURRENT = True
#docs: https://github.com/fondberg/easee_hass

"""
This is the class that implements a specific chargertype into peaqev.
Note that you need to change:

-manifest.json: add the domain of the charger to after_dependencies
-constants.py: alter the CHARGERTYPES with a new type-constant for your charger. If not, it will not be selectable in config_flow
-chargertypes.py|init: update the clause with your type to return this class as the charger.
"""

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

        on_off_params = {
            "charger_id": self._chargerid
        }

        if self._auth_required is True:
            _on = "start"
            _off = "stop"
        else:
            _on = "resume"
            _off = "pause"

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call=_on,
            off_call=_off,
            pause_call="pause",
            resume_call="resume",
            on_off_params=on_off_params,
            allowupdatecurrent=True,
            update_current_call="set_charger_dynamic_limit",
            update_current_params=servicecall_params
        )
