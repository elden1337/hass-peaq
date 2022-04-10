from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = ["_power", "_1", "_2", "_status", "_dimmer", "_downlight", "_current", "_voltage"]
DOMAIN = "chargeamps"

class ChargeAmps(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass, currentupdate=True)
        self._chargerid = chargerid
        self.getentities(DOMAIN, ENTITYENDINGS)
        self._chargerstates["idle"] = ["available"]
        self._chargerstates["connected"] = ["connected"]
        self._chargerstates["charging"] = ["charging"]
        self.chargerentity = f"sensor.{self._entityschema}_1"
        self.powermeter = f"sensor.{self._entityschema}_1_power"
        self.powerswitch = f"switch.{self._entityschema}_1"
        self.ampmeter = "Max current"
        self.ampmeter_is_attribute = True

        servicecall_params = {
            "charger": "chargepoint",
            "chargerid": self._chargerid,
            "current": "max_current"
        }

        self._set_servicecalls(DOMAIN, "start", "stop", None, None, "set_max_current", servicecall_params)
