import custom_components.peaq.constants as constants
import homeassistant.helpers.template as template
from homeassistant.core import HomeAssistant
import logging
import json

_LOGGER = logging.getLogger(__name__)

"""Init the service"""
class ChargerTypeData():
    def __init__(self, hass: HomeAssistant, input, chargerid):
        self._charger = None
        self._type = input
        self._hass = hass
        self._chargerid = chargerid

        if input == constants.CHARGERTYPE_CHARGEAMPS:
            self._charger = ChargeAmps(self._hass, self._chargerid)
        elif  input == constants.CHARGERTYPE_EASEE:
            self._charger = Easee(self._hass, self._chargerid)

        self.validatecharger()

    @property
    def type(self) -> str:
        return self._type

    @property
    def charger(self):
        return self._charger

    def validatecharger(self):
        try:
            assert self._charger.chargerentity.len > 0
            assert self._charger.powermeter.len > 0
            assert self._charger.powerswitch.len > 0
            assert self._charger.servicecalls["domain"] is not None
            assert self._charger.servicecalls["on"] is not None
            assert self._charger.servicecalls["off"] is not None
            if self._charger.allowupdatecurrent:
                assert self._charger.servicecalls["updatecurrent"] is not None
        except:
            pass

class ChargerBase():
    def __init__(self):
        self._chargerEntity = None
        self._powermeter = None
        self._powerswitch = None
        self._allowupdatecurrent = False
        self._servicecalls = {}
        self._chargerstates = {
            "idle": [],
            "connected": [],
            "charging": []
        }
        
    @property
    def chargerstates(self) -> dict:
        return self._chargerstates

    @property
    def allowupdatecurrent(self) -> bool:
        return self._allowupdatecurrent

    """Power meter"""
    @property
    def powermeter(self):
        return self._powermeter

    @powermeter.setter
    def powermeter(self, val):
        assert type(val) is str
        self._powermeter = val

    """Power Switch"""
    @property
    def powerswitch(self):
        return self._powerswitch

    @powerswitch.setter
    def powerswitch(self, val):
        assert type(val) is str
        self._powerswitch = val

    """Charger entity"""
    @property
    def chargerentity(self):
        return self._chargerentity

    @chargerentity.setter
    def chargerentity(self, val):
        assert type(val) is str
        self._chargerentity = val

    """Service calls"""
    @property
    def servicecalls(self) -> dict:
        return self._servicecalls

    @servicecalls.setter
    def servicecalls(self, obj):
        assert type(obj) is dict
        self._servicecalls = obj

class ChargeAmps(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__()
        self._chargerid = chargerid
        self._allowupdatecurrent = True
        self._setchargerstates()
        self._getentities()

    def _setchargerstates(self):
        self._chargerstates["idle"] = ["available"]
        self._chargerstates["connected"] = ["connected"]
        self._chargerstates["charging"] = ["charging"]

    def _getentities(self):
        self.chargerentity = f"sensor.{self._chargerid}_1"
        self.powermeter = f"sensor.{self._chargerid}_1_power"
        self.powerswitch = f"switch.{self._chargerid}_1"
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
   
class Easee(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        self._hass = hass
        super().__init__()
        self._chargerid = chargerid
        self._allowupdatecurrent = True
        self._setchargerstates()
        self._getentities(self._hass)
        
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

    def _getentities(self, hass):
        entities = template.integration_entities(hass, "easee")
        
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
            self.servicecalls = {
                "domain": "easee",
                "on": "start",
                "off": "stop",
                "updatecurrent": {
                   "name": "set_charger_max_limit",
                   "params": {
                       "charger": "charger_id",
                       "chargerid": self._chargerid,
                       "current": "current"
                       }
                }
            }


