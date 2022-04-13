from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from custom_components.peaqev.peaqservice.util.chargerstates import CHARGECONTROLLER
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)
import logging
from homeassistant.core import HomeAssistant

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


class Easee(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass)
        self._chargerid = chargerid
        self.getentities(DOMAINNAME, ENTITYENDINGS)
        self._chargerstates[CHARGECONTROLLER.Idle] = ["disconnected"]
        self._chargerstates[CHARGECONTROLLER.Connected] = ["awaiting_start", "ready_to_charge"]
        self._chargerstates[CHARGECONTROLLER.Charging] = ["charging"]
        self.chargerentity = f"sensor.{self._entityschema}_status"
        self.powermeter = f"sensor.{self._entityschema}_power"
        self.powerswitch = f"switch.{self._entityschema}_is_enabled"
        self.ampmeter = f"sensor.{self._entityschema}_max_charger_limit"
        self.ampmeter_is_attribute = False

        servicecall_params = {}
        servicecall_params[CHARGER] = "charger_id"
        servicecall_params[CHARGERID] = self._chargerid
        servicecall_params[CURRENT] = "current"

        self._set_servicecalls(DOMAINNAME, "start", "stop", "pause", "resume", "set_charger_max_limit", servicecall_params)



