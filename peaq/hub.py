import logging
from datetime import datetime

import custom_components.peaq.peaq.extensionmethods as ex
from custom_components.peaq.peaq.chargecontroller import ChargeController
from custom_components.peaq.peaq.prediction import Prediction
from custom_components.peaq.peaq.threshold import Threshold
from custom_components.peaq.peaq.locale import LocaleData
from custom_components.peaq.peaq.chargertypes import ChargerTypeData
from homeassistant.helpers.event import async_track_state_change
from homeassistant.core import (
    HomeAssistant,
    callback,
)

_LOGGER = logging.getLogger(__name__)

"""
todo:
fixa så att elmätare inte inkluderar laddare (om bool)
fixa config flow med månaderna och nonhours
fixa updatecurrent
fixa easee
refactorera alla members i hub, stökigt nu (gör miniclass med sökande sensor och property)
"""

class Hub:
    NAME = "Peaq"  #hardcoded, get from domain instead
    HUB_ID = 1342
    CONSUMPTION_INTEGRAL_NAME = "Energy excluding car"
    CONSUMPTION_TOTAL_NAME = "Energy including car" 

    """for getters and setters internals"""
    _powersensor = 0
    _TotalHourlyEnergy = 0
    _chargerobject = ""
    _chargerobject_switch = ""
    _carpowersensor = 0
    _charger_done = False
    """for getters and setters internals"""

    def __init__(
        self, 
        hass: HomeAssistant, 
        configInputs: dict
        ):
        self.hass = hass
        
        """from the config inputs"""
        self.LocaleData = LocaleData(configInputs["locale"])
        self.chargertypedata = ChargerTypeData(hass, configInputs["chargertype"])
        self._powersensor_includes_car = configInputs["powersensorincludescar"]
        self._monthlystartpeak = configInputs["monthlystartpeak"]
        self.nonhours = configInputs["nonhours"]
        self.CautionHours = configInputs["cautionhours"]
        self.powersensorentity = self._SetPowerSensors(configInputs["powersensor"])
        """from the config inputs"""
       
        self.chargerenabled = HubMember(bool, "binary_sensor.peaq_charger_enabled", False)  #hardcoded, fix
        #self.chargerenabled.value = False

        self.ChargingDone_Entity = "binary_sensor.peaq_charging_done"  #hardcoded, fix
        self.TotalHourlyEnergy_Entity = f"sensor.{self.NAME.lower()}_{ex.NameToId(self.CONSUMPTION_TOTAL_NAME)}_hourly" #ugly, fix probably
   
        self.powersensormovingaverage = HubMember(int, "sensor.peaq_average_consumption", 0) #hardcoded, fix
        
        """Init the subclasses"""
        self.TotalPowerSensor = MiniSensor("Total Power")
        self.Prediction = Prediction(self)
        self.Threshold = Threshold(self)
        self.chargecontroller = ChargeController(self)
        """Init the subclasses"""

        self.currentpeak = CurrentPeak(float, "sensor.peaq_monthly_max_peak_min_of_three", 0, self._monthlystartpeak[datetime.now().month]) #hardcoded, fix

        #init values
        self.ChargerObject = self.hass.states.get(self.chargertypedata.charger.chargerentity)
        self.ChargerObject_Switch = self.hass.states.get(self.chargertypedata.charger.powerswitch)
        self.CarPowerSensor = self.hass.states.get(self.chargertypedata.charger.powermeter)
        self.TotalEnergyThisHour = self.hass.states.get(self.TotalHourlyEnergy_Entity)
        self.currentpeak.value = self.hass.states.get(self.currentpeak.entity)
        #init values
        
        trackerEntities = [
            self.chargertypedata.charger.powermeter,
            self.chargertypedata.charger.powerswitch,
            self.powersensorentity,
            self.TotalHourlyEnergy_Entity,
            self.currentpeak.entity
        ]

        #mocks in this one. make them work generic
        self.chargingTrackerEntities = [self.powersensormovingaverage.entity, self.chargerenabled.entity, self.ChargingDone_Entity, self.chargertypedata.charger.chargerentity, "sensor.peaq_chargercontroller"]
        self.chargerblocked = False
        self.chargerStart = False
        self.chargerStop = False
        #mocks in this one. make them work generic

        trackerEntities += self.chargingTrackerEntities
        
        async_track_state_change(hass, trackerEntities, self.state_changed)
    
    @property
    def ChargerEntity(self):
        return self._chargerobject

    @ChargerEntity.setter
    def ChargerEntity(self, value):
        self._chargerobject = value

    @property
    def ChargerEntity_Switch(self):
        return self._chargerobject_switch

    @ChargerEntity_Switch.setter
    def ChargerEntity_Switch(self, value):
        self._chargerobject_switch = value        

    """Total hourly energy"""
    @property
    def TotalEnergyThisHour(self):
        return self._TotalHourlyEnergy

    @TotalEnergyThisHour.setter
    def TotalEnergyThisHour(self, value):
        if ex.Is_Float(value):
            self._TotalHourlyEnergy = float(value)

    """House powersensor"""
    @property
    def powersensor(self):
        return self._powersensor

    @powersensor.setter
    def powersensor(self, value):
        if ex.Is_Float(value):
            self._powersensor = int(float(value))

    """Car powersensor"""
    @property
    def carpowersensor(self):
        if self._carpowersensor is None:
            return 0
        else:
            return self._carpowersensor

    @carpowersensor.setter
    def carpowersensor(self, value):
        if ex.Is_Float(value):
            self._carpowersensor = int(float(value))

    """Charging Done"""
    @property
    def ChargingDone(self) -> bool:
        return self._charger_done

    @ChargingDone.setter
    def ChargingDone(self, value):
        self._charger_done = True if value.lower() == "on" else False

    def _SetPowerSensors(self, powerSensorName) -> str: 
        if powerSensorName.startswith("sensor."):
            return powerSensorName
        else:
            return "sensor." + powerSensorName

    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        try:
            if old_state is None or old_state.state != new_state.state:
                await self._UpdateSensor(entity_id, new_state.state)
        except Exception as e:
            _LOGGER.warn("Unable to handle data: ", entity_id, e)
            pass

    async def _UpdateSensor(self,entity,value):
        if entity == self.powersensorentity:
            self.powersensor = value
            self.TotalPowerSensor.State = (self.powersensor + self.carpowersensor)
        elif entity == self.chargertypedata.charger.chargerentity:
            self.ChargerEntity = value
        elif entity == self.chargertypedata.charger.powermeter:
            self.carpowersensor = value
            self.TotalPowerSensor.State = (self.carpowersensor + self.powersensor)
        elif entity == self.chargertypedata.charger.powerswitch:
            self.ChargerEntity_Switch = value
        elif entity == self.currentpeak.entity:
            self.currentpeak.value = value
        elif entity == self.TotalHourlyEnergy_Entity:
            self.TotalEnergyThisHour = value
        elif entity == self.powersensormovingaverage.entity:
            self.powersensormovingaverage.value = value
        
        if entity in self.chargingTrackerEntities and not self.chargerblocked:
            await self._Charge(self.chargertypedata.charger.servicecalls['domain'], self.chargertypedata.charger.servicecalls['on'], self.chargertypedata.charger.servicecalls['off'])
            
    async def _Charge(self, domain:str, call_on:str, call_off:str):
        self.chargerblocked = True
        if self.chargerenabled.value == True:
            if self.chargecontroller.status.name == "Start":
                if self.ChargerEntity_Switch == "off" and self.chargerStart == False: 
                    self.chargerStart = True
                    self.chargerStop = False
                    await self.hass.services.async_call(domain,call_on)
            elif self.chargecontroller.status.name == "Stop" or self.ChargingDone == True or self.chargecontroller.status.name == "Idle":
                if self.ChargerEntity_Switch == "on" and self.chargerStop == False:
                    self.chargerStop = True
                    self.chargerStart = False 
                    await self.hass.services.async_call(domain, call_off)              
        else: 
           if self.ChargerEntity_Switch == "on" and self.chargerStop == False:
                self.chargerStop = True
                self.chargerStart = False
                await self.hass.services.async_call(domain, call_off)  
        self.chargerblocked = False

#this can probably be removed in favor of HubMember-class
class MiniSensor: 
    def __init__(self, name):
        self.Name = name
        self.Id = ex.NameToId(self.Name)
        self._state = 0

    @property   
    def State(self):
        return self._state

    @State.setter
    def State(self, value):
        self._state = int(float(value))
#this can probably be removed in favor of HubMember-class

class HubMember:
    def __init__(self, type: type, listenerentity = None, initval = None):
        self._value = initval
        self._type = type
        self._listenerentity = listenerentity

    @property
    def entity(self):
        return self._listenerentity

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if type(value) is self._type:
            self._value = value
        elif self._type is int:
            self._value = int(float(value))
        elif self._type is bool:
            if value.lower() == "on":
                self._value = True
            elif value.lower() == "off":
                self._value = False
        elif  self._type is str:
            self._value = str(value)

class CurrentPeak(HubMember):
    def __init__(self, type: type, listenerentity, initval, startpeak):
        self._startpeak = startpeak
        self._value = initval
        super().__init__(type, listenerentity, initval)

    @HubMember.value.getter
    def value(self):
        return max(self._value, float(self._startpeak)) if self._value is not None else float(self._startpeak)

