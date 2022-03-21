import custom_components.peaq.peaq.constants as constants
import homeassistant.helpers.template as template
from homeassistant.core import HomeAssistant
import logging
import json

_LOGGER = logging.getLogger(__name__)

"""Init the service"""
class ChargerTypeData():
    def __init__(self, hass: HomeAssistant, input):
        self._Charger = None
        self._Type = input
        self._hass = hass

        if input == constants.CHARGERTYPE_CHARGEAMPS:
            self.Charger = ChargeAmps(self._hass)
        elif  input == constants.CHARGERTYPE_EASEE:
            self.Charger = Easee(self._hass)
    
    @property
    def Type(self) -> str:
        return self._Type

    @property
    def Charger(self):
        return self._Charger

    @Charger.setter
    def Charger(self, obj):
        self._Charger = obj

"""Shared baseclass"""
class ChargerTypeBase():
    def __init__(self):
        self._PowerMeter = ""
        self._PowerSwitch = ""
        self._ChargerEntity = ""
        self._ServiceCalls = {}     

    """Power meter"""
    @property
    def PowerMeter(self):
        return self._PowerMeter

    @PowerMeter.setter
    def PowerMeter(self, val):
        assert type(val) is str
        self._PowerMeter = val

    """Power Switch"""
    @property
    def PowerSwitch(self):
        return self._PowerSwitch

    @PowerSwitch.setter
    def PowerSwitch(self, val):
        assert type(val) is str
        self._PowerSwitch = val

    """Charger entity"""
    @property
    def ChargerEntity(self):
        return self._ChargerEntity

    @ChargerEntity.setter
    def ChargerEntity(self, val):
        assert type(val) is str
        self._ChargerEntity = val

    """Service calls"""
    @property
    def ServiceCalls(self) -> dict:
        return self._ServiceCalls

    @ServiceCalls.setter
    def ServiceCalls(self, obj):
        assert type(obj) is dict
        self._ServiceCalls = obj

class ChargeAmps():
    def __init__(self, hass: HomeAssistant):
        self._hass = hass
        self._ChargerEntity = None
        self._PowerMeter = None
        self._PowerSwitch = None
        # self.ChargerEntity = "sensor.hake_2012019145m_1"
        # self.PowerMeter = "sensor.hake_2012019145m_1_power"
        # self.PowerSwitch = "switch.hake_2012019145m_1" 
        self.ServiceCalls = {}
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

            self.ChargerEntity = f"sensor.{candidate}_1"
            self.PowerMeter = f"sensor.{candidate}_1_power"
            self.PowerSwitch = f"switch.{candidate}_1"

        # ret = {
        #     "powersensor": powersensor,
        #     "switch": switch,
        #     "mainsensor":mainsensor
        # }
        
        # return ret
    
    """Power meter"""
    @property
    def PowerMeter(self):
        return self._PowerMeter

    @PowerMeter.setter
    def PowerMeter(self, val):
        assert type(val) is str
        self._PowerMeter = val

    """Power Switch"""
    @property
    def PowerSwitch(self):
        return self._PowerSwitch

    @PowerSwitch.setter
    def PowerSwitch(self, val):
        assert type(val) is str
        self._PowerSwitch = val

    """Charger entity"""
    @property
    def ChargerEntity(self):
        return self._ChargerEntity

    @ChargerEntity.setter
    def ChargerEntity(self, val):
        assert type(val) is str
        self._ChargerEntity = val

    """Service calls"""
    @property
    def ServiceCalls(self) -> dict:
        return self._ServiceCalls

    @ServiceCalls.setter
    def ServiceCalls(self, obj):
        assert type(obj) is dict
        self._ServiceCalls = obj

class Easee(ChargerTypeBase):
    def __init__(self):
        super().__init__()
