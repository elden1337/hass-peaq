import logging
from datetime import datetime

import custom_components.peaq.peaq.extensionmethods as ex
import custom_components.peaq.peaq.constants as constants
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
"""

class Hub:
    hub_id = 1342
    
    def __init__(
        self, 
        hass: HomeAssistant, 
        config_inputs: dict,
        domain: str
        ):
        self.hass = hass
        self.hubname = domain

        """from the config inputs"""
        self.localedata = LocaleData(config_inputs["locale"])
        self.chargertypedata = ChargerTypeData(hass, config_inputs["chargertype"])
        self._powersensor_includes_car = config_inputs["powersensorincludescar"]
        self._monthlystartpeak = config_inputs["monthlystartpeak"]
        self.nonhours = config_inputs["nonhours"]
        self.cautionhours = config_inputs["cautionhours"]
        """from the config inputs"""
       
        self.powersensor = HubMember(int, config_inputs["powersensor"], 0)
        self.chargerenabled = HubMember(bool, "binary_sensor.peaq_charger_enabled", False)  #hardcoded, fix
        self.powersensormovingaverage = HubMember(int, "sensor.peaq_average_consumption", 0) #hardcoded, fix
        self.totalhourlyenergy = HubMember(float, f"sensor.{self.hubname.lower()}_{ex.NameToId(constants.CONSUMPTION_TOTAL_NAME)}_hourly", 0) #ugly, fix probably
        self.charger_done = HubMember(bool, "binary_sensor.peaq_charging_done", False) #hardcoded, fix
        self.totalpowersensor = HubMember(int, name = constants.TOTALPOWER)
        self.carpowersensor = HubMember(int, self.chargertypedata.charger.powermeter, 0)
        self.currentpeak = CurrentPeak(float, "sensor.peaq_monthly_max_peak_min_of_three", 0, self._monthlystartpeak[datetime.now().month]) #hardcoded, fix
        self.chargerobject = HubMember(str, self.chargertypedata.charger.chargerentity)
        self.chargerobject_switch = ChargerSwitch(str, self.chargertypedata.charger.powerswitch, "", "Max current") #hardcoded, fix in chargertypes.
        """Init the subclasses"""
        self.prediction = Prediction(self)
        self.threshold = Threshold(self)
        self.chargecontroller = ChargeController(self)
        """Init the subclasses"""
        
        #init values
        self.chargerobject.value = self.hass.states.get(self.chargerobject.entity)
        self.chargerobject_switch.value = self.hass.states.get(self.chargerobject_switch.entity)
        self.carpowersensor.value = self.hass.states.get(self.carpowersensor.entity)
        self.totalhourlyenergy.value = self.hass.states.get(self.totalhourlyenergy.entity)
        self.currentpeak.value = self.hass.states.get(self.currentpeak.entity)
        #init values
        
        trackerEntities = [
            self.carpowersensor.entity,
            self.chargerobject_switch.entity,
            self.powersensor.entity,
            self.totalhourlyenergy.entity,
            self.currentpeak.entity
        ]

        self.chargingtracker_entities = [
            self.powersensormovingaverage.entity, 
            self.chargerenabled.entity, 
            self.charger_done.entity, 
            self.chargerobject.entity,
            "sensor.peaq_chargercontroller" #hardcoded, fix
            ]

        #remove?
        self.chargerblocked = False
        self.chargerStart = False
        self.chargerStop = False
        #remove?
        trackerEntities += self.chargingtracker_entities
        
        async_track_state_change(hass, trackerEntities, self.state_changed)
 
    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        try:
            if old_state is None or old_state.state != new_state.state:
                await self._UpdateSensor(entity_id, new_state.state)
        except Exception as e:
            _LOGGER.warn("Unable to handle data: ", entity_id, e)
            pass

    async def _UpdateSensor(self,entity,value):
        if entity == self.powersensor.entity:
            self.powersensor.value = value
            self.totalpowersensor.value = (self.powersensor.value + self.carpowersensor.value)
        elif entity == self.chargerobject.entity:
            self.chargerobject.value = value
        elif entity == self.carpowersensor.entity:
            self.carpowersensor.value = value
            self.totalpowersensor.value = (self.carpowersensor.value + self.powersensor.value)
        elif entity == self.chargerobject_switch.entity:
            self.chargerobject_switch.value = value
            self.chargerobject_switch.current = str(hass.states.get(self.chargerobject_switch.entity).attributes.get(self.chargerobject_switch._current_attr_name))
        elif entity == self.currentpeak.entity:
            self.currentpeak.value = value
        elif entity == self.totalhourlyenergy.entity:
            self.totalhourlyenergy.value = value
        elif entity == self.powersensormovingaverage.entity:
            self.powersensormovingaverage.value = value
        
        if entity in self.chargingtracker_entities and not self.chargerblocked:
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

class HubMember:
    def __init__(self, type: type, listenerentity = None, initval = None, name = None):
        self._value = initval
        self._type = type
        self._listenerentity = listenerentity
        self.name = name
        self.id = ex.NameToId(self.name) if self.name is not None else None

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
            self._value = int(float(value)) if value is not None else 0
        elif self._type is bool:
            if value is None:
                self._value = False
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

class ChargerSwitch(HubMember):
    def __init__(self, type: type, listenerentity, initval, currentname):
        self._value = initval
        self._current = 6
        self._current_attr_name = currentname
        super().__init__(type, listenerentity, initval)

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        if value is not None:
            self._current = int(value)



    