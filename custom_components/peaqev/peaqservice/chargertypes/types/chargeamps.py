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

ENTITYENDINGS = ["_power", "_1", "_2", "_status", "_dimmer", "_downlight", "_current", "_voltage"]
DOMAINNAME = "chargeamps"
UPDATECURRENT = True
#docs: https://github.com/kirei/hass-chargeamps

"""
This is the class that implements a specific chargertype into peaqev.
Note that you need to change:

-manifest.json: add the domain of the charger to after_dependencies
-constants.py: alter the CHARGERTYPES with a new type-constant for your charger. If not, it will not be selectable in configflow
-chargertypes.py|init: update the clause with your type to return this class as the charger.
"""


class ChargeAmps(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass)
        self._chargerid = chargerid
        self._chargeamps_connector = 1
        self.getentities(DOMAINNAME, ENTITYENDINGS)
        self._chargerstates[CHARGERSTATES.Idle] = ["available"]
        self._chargerstates[CHARGERSTATES.Connected] = ["connected"]
        self._chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self._chargerstates[CHARGERSTATES.Done] = ["not_available"]
        self.chargerentity = f"sensor.{self._entityschema}_1"
        self.powermeter = f"sensor.{self._entityschema}_1_power"
        self.powerswitch = f"switch.{self._entityschema}_1"
        self.ampmeter = "max_current"
        self.ampmeter_is_attribute = True

        servicecall_params = {}
        servicecall_params[CHARGER] = "chargepoint"
        servicecall_params[CHARGERID] = self._chargerid
        servicecall_params[CURRENT] = "max_current"

        _on_off_params = {
            "chargepoint": self._chargerid,
            "connector": self._chargeamps_connector
        }

        _on = CallType("enable", _on_off_params)
        _off = CallType("disable", _on_off_params)

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call=_on,
            off_call=_off,
            allowupdatecurrent= UPDATECURRENT,
            update_current_call="set_max_current",
            update_current_params=servicecall_params
        )
