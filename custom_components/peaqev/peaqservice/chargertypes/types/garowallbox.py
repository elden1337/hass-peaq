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

ENTITYENDINGS = [] #fix
DOMAINNAME = "garo_wallbox"
UPDATECURRENT = True


class GaroWallbox(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass)
        self._chargerid = chargerid
        self.getentities(DOMAINNAME, ENTITYENDINGS)
        self._chargerstates[CHARGECONTROLLER.Idle] = [] #fix
        self._chargerstates[CHARGECONTROLLER.Connected] = [] #fix
        self._chargerstates[CHARGECONTROLLER.Charging] = [] #fix
        #self.chargerentity = f"sensor.{self._entityschema}_1"
        #self.powermeter = f"sensor.{self._entityschema}_1_power"
        #self.powerswitch = f"switch.{self._entityschema}_1"
        #self.ampmeter = "Max current"
        #self.ampmeter_is_attribute = True

        servicecall_params = {}
        servicecall_params[CHARGER] = "entity_id"
        servicecall_params[CHARGERID] = self._chargerid #sensor for garo, not id
        servicecall_params[CURRENT] = "limit"

        self._set_servicecalls(DOMAINNAME, "set_mode|on", "set_mode|off", None, None, "set_current_limit", servicecall_params)
        #remember to fix a split on modes in servicalls.py on |. example here. same call for both on and off, but with different params.
