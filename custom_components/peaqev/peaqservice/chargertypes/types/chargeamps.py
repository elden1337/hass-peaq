import logging

from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from custom_components.peaqev.peaqservice.util.chargerstates import CHARGECONTROLLER
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = ["_power", "_1", "_2", "_status", "_dimmer", "_downlight", "_current", "_voltage"]
DOMAINNAME = "chargeamps"
UPDATECURRENT = True


class ChargeAmps(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass)
        self._chargerid = chargerid
        self.getentities(DOMAINNAME, ENTITYENDINGS)
        self._chargerstates[CHARGECONTROLLER.Idle] = ["available"]
        self._chargerstates[CHARGECONTROLLER.Connected] = ["connected"]
        self._chargerstates[CHARGECONTROLLER.Charging] = ["charging"]
        self.chargerentity = f"sensor.{self._entityschema}_1"
        self.powermeter = f"sensor.{self._entityschema}_1_power"
        self.powerswitch = f"switch.{self._entityschema}_1"
        self.ampmeter = "max_current"
        self.ampmeter_is_attribute = True

        servicecall_params = {}
        servicecall_params[CHARGER] = "chargepoint"
        servicecall_params[CHARGERID] = self._chargerid
        servicecall_params[CURRENT] = "max_current"

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call="enable",
            off_call="disable",
            allowupdatecurrent= True,
            update_current_call="set_max_current",
            update_current_params=servicecall_params
        )
