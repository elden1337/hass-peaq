from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
import logging
import homeassistant.helpers.template as template
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class Easee(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass, currentupdate=True)
        self._chargerid = chargerid
        self._setchargerstates()
        self._getentities()

    # disconnected
    # awaiting_start
    # charging
    # ready_to_charge
    # completed
    # error

    def _setchargerstates(self):
        self._chargerstates["idle"] = ["disconnected"]
        self._chargerstates["connected"] = ["awaiting_start", "ready_to_charge"]
        self._chargerstates["charging"] = ["charging"]

    def _getentities(self):
        entities = template.integration_entities(self._hass, "easee")

        if len(entities) < 1:
            _LOGGER.error("no entities!")
        else:
            _endings = [
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

            namelrg = entities[0].split(".")
            candidate = ""

            for e in _endings:
                if namelrg[1].endswith(e):
                    candidate = namelrg[1].replace(e, '')

            self.chargerentity = f"sensor.{candidate}_status"
            self.powermeter = f"sensor.{candidate}_power"
            self.powerswitch = f"switch.{candidate}_is_enabled"
            self.ampmeter = f"sensor.{candidate}_max_charger_limit"
            self.ampmeter_is_attribute = False
            self.servicecalls = {
                "domain": "easee",
                "on": "start",
                "off": "stop",
                "pause": "pause",
                "resume": "resume",
                "updatecurrent": {
                    "name": "set_charger_max_limit",
                    "params": {
                        "charger": "charger_id",
                        "chargerid": self._chargerid,
                        "current": "current"
                    }
                }
            }
