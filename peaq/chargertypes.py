import custom_components.peaq.peaq.constants as constants
import homeassistant.helpers.template as template
from homeassistant.core import HomeAssistant
import logging
import json

_LOGGER = logging.getLogger(__name__)

"""Init the service"""
class ChargerTypeData():
    def __init__(self, hass: HomeAssistant, input):
        self._charger = None
        self._type = input
        self._hass = hass

        if input == constants.CHARGERTYPE_CHARGEAMPS:
            self._charger = ChargeAmps(self._hass)
        elif  input == constants.CHARGERTYPE_EASEE:
            self._charger = Easee(self._hass)
    
    @property
    def type(self) -> str:
        return self._type

    @property
    def charger(self):
        return self._charger

class ChargeAmps():
    def __init__(self, hass: HomeAssistant):
        self._hass = hass
        self._chargerEntity = None
        self._powermeter = None
        self._powerswitch = None
        self._servicecalls = {}
        self.GetEntities(self._hass)
        #super().__init__()

    def GetEntities(self, hass):
        entities = template.integration_entities(hass, "chargeamps")
        
        if len(entities) < 1:
            _LOGGER.error("no entities!")
        else:
            _endings = ["_power","_total_energy","_dimmer","_downlight"]

            namelrg = entities[0].split(".")
            candidate = ""

            for e in _endings:
                if namelrg[1].endswith(e):
                    candidate = namelrg[1].replace(e, '') 

            self.chargerentity = f"sensor.{candidate}_1"
            self.powermeter = f"sensor.{candidate}_1_power"
            self.powerswitch = f"switch.{candidate}_1"
            self.servicecalls = {
                "domain": "chargeamps",
                "on": "enable",
                "off": "disable",
                "updatecurrent": {
                   "name": "set_max_current",
                   "param": "max_current"
                }
            }
    
    @property
    def allowupdatecurrent(self) -> bool:
        return True

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

class Easee():
    def __init__(self):
        pass
