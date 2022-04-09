from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
import logging
import homeassistant.helpers.template as template
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class ChargeAmps(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass, currentupdate=True)
        self._chargerid = chargerid
        self._setchargerstates()
        self._getentities()

    def _setchargerstates(self):
        self._chargerstates["idle"] = ["available"]
        self._chargerstates["connected"] = ["connected"]
        self._chargerstates["charging"] = ["charging"]

    def _getentities(self):
        entities = template.integration_entities(self._hass, "chargeamps")

        if len(entities) < 1:
            _LOGGER.error("no entities!")
        else:
            _endings = [
                "_power",
                "_1",
                "_2",
                "_status",
                "_dimmer",
                "_downlight",
                "_current",
                "_voltage",
            ]

            namelrg = entities[0].split(".")
            candidate = ""

            for e in _endings:
                if namelrg[1].endswith(e):
                    candidate = namelrg[1].replace(e, '')

            self.chargerentity = f"sensor.{candidate}_1"
            self.powermeter = f"sensor.{candidate}_1_power"
            self.powerswitch = f"switch.{candidate}_1"
            self.ampmeter = "Max current"
            self.ampmeter_is_attribute = True
            self.servicecalls = {
                "domain": "chargeamps",
                "on": "enable",
                "off": "disable",
                "updatecurrent": {
                    "name": "set_max_current",
                    "params": {
                        "charger": "chargepoint",
                        "chargerid": self._chargerid,
                        "current":"max_current"
                        }
                }
            }