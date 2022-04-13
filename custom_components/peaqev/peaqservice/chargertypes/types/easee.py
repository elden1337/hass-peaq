from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from custom_components.peaqev.peaqservice.util.chargerstates import CHARGECONTROLLER
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGERTYPEHELPERS_CHARGER,
    CHARGERTYPEHELPERS_CHARGERID,
    CHARGERTYPEHELPERS_CURRENT,
)
import logging
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = ["_power", "_status", "_dimmer", "_downlight", "_lifetime_energy", "_online", "_current", "_voltage", "_output_limit", "_cost_per_kwh", "_enable_idle_current"]
DOMAIN = "easee"


class Easee(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass, currentupdate=True)
        self._chargerid = chargerid
        self.getentities(DOMAIN, ENTITYENDINGS)
        self._chargerstates[CHARGECONTROLLER.Idle] = ["disconnected"]
        self._chargerstates[CHARGECONTROLLER.Connected] = ["awaiting_start", "ready_to_charge"]
        self._chargerstates[CHARGECONTROLLER.Charging] = ["charging"]
        self.chargerentity = f"sensor.{self._entityschema}_status"
        self.powermeter = f"sensor.{self._entityschema}_power"
        self.powerswitch = f"switch.{self._entityschema}_is_enabled"
        self.ampmeter = f"sensor.{self._entityschema}_max_charger_limit"
        self.ampmeter_is_attribute = False

        servicecall_params = {}
        servicecall_params[CHARGERTYPEHELPERS_CHARGER] = "charger_id"
        servicecall_params[CHARGERTYPEHELPERS_CHARGERID] = self._chargerid
        servicecall_params[CHARGERTYPEHELPERS_CURRENT] = "current"

        self._set_servicecalls(DOMAIN, "start", "stop", "pause", "resume", "set_charger_max_limit", servicecall_params)



