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

class Hub:
    NAME = "Peaq"
    HUB_ID = 1342
    CONSUMPTION_INTEGRAL_NAME = "Energy excluding car"
    CONSUMPTION_TOTAL_NAME = "Energy including car" 

    """for getters and setters internals"""
    _CurrentPeakSensor = 0 #sensor
    _PowerSensor = 0
    _TotalHourlyEnergy = 0
    _PowerSensorMovingAverage = 0
    _ChargerObject = ""
    _ChargerObject_Switch = ""
    _CarPowerSensor = 0
    _ChargerEnabled = False
    _ChargingDone = False
    """for getters and setters internals"""

    def __init__(
        self, 
        hass: HomeAssistant, 
        configInputs: dict
        ):
        self.hass = hass
        
        """from the config inputs"""
        self.LocaleData = LocaleData(configInputs["locale"])
        self.ChargerTypeData = ChargerTypeData(hass, configInputs["chargertype"])
        self._powersensor_includes_car = configInputs["powersensorincludescar"]
        self._monthlystartpeak = configInputs["monthlystartpeak"]
        self.NonHours = configInputs["nonhours"]
        self.CautionHours = configInputs["cautionhours"]
        self.powersensorentity = self._SetPowerSensors(configInputs["powersensor"])
        """from the config inputs"""
        
        self.currentPeaksensorentity = "sensor.peaq_monthly_max_peak_min_of_three" #mock, fix later
        self.ChargerEnabled_Entity = "binary_sensor.peaq_charger_enabled" #mock, fix later
        self.ChargingDone_Entity = "binary_sensor.peaq_charging_done" #mock, fix later
        self.TotalHourlyEnergy_Entity = f"sensor.{self.NAME.lower()}_{ex.NameToId(self.CONSUMPTION_TOTAL_NAME)}_hourly" #ugly, fix probably

        self.PowerSensorMovingAverage_Entity = "sensor.peaq_average_consumption"       

        """Init the subclasses"""
        self.TotalPowerSensor = MiniSensor("Total Power")
        self.Prediction = Prediction(self)
        self.Threshold = Threshold(self)
        self.ChargeController = ChargeController(self)
        """Init the subclasses"""

        #init values
        self.ChargerObject = self.hass.states.get(self.ChargerTypeData.Charger.ChargerEntity)
        self.ChargerObject_Switch = self.hass.states.get(self.ChargerTypeData.Charger.PowerSwitch)
        self.CarPowerSensor = self.hass.states.get(self.ChargerTypeData.Charger.PowerMeter)
        self.TotalEnergyThisHour = self.hass.states.get(self.TotalHourlyEnergy_Entity)
        #init values
        
        trackerEntities = [
            self.ChargerTypeData.Charger.PowerMeter,
            self.ChargerTypeData.Charger.PowerSwitch,
            self.powersensorentity,
            self.TotalHourlyEnergy_Entity,
            self.currentPeaksensorentity
        ]

        #mocks in this one. make them work generic
        self.chargingTrackerEntities = [self.PowerSensorMovingAverage_Entity, self.ChargerEnabled_Entity, self.ChargingDone_Entity, self.ChargerTypeData.Charger.ChargerEntity, "sensor.peaq_chargercontroller"]
        self.chargerblocked = False
        #mocks in this one. make them work generic

        trackerEntities += self.chargingTrackerEntities
        
        async_track_state_change(hass, trackerEntities, self.state_changed)
    
    @property
    def ChargerEntity(self):
        return self._ChargerObject

    @ChargerEntity.setter
    def ChargerEntity(self, value):
        self._ChargerObject = value

    @property
    def ChargerEntity_Switch(self):
        return self._ChargerObject_Switch

    @ChargerEntity_Switch.setter
    def ChargerEntity_Switch(self, value):
        self._ChargerObject_Switch = value
        
    """Moving average house powersensor"""
    @property
    def PowerSensorMovingAverage(self):
        return self._PowerSensorMovingAverage

    @PowerSensorMovingAverage.setter
    def PowerSensorMovingAverage(self, value):
        if ex.Is_Float(value):
            self._PowerSensorMovingAverage = int(float(value))

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
        return self._PowerSensor

    @powersensor.setter
    def powersensor(self, value):
        if ex.Is_Float(value):
            self._PowerSensor = int(float(value))

    """Car powersensor"""
    @property
    def carpowersensor(self):
        if self._CarPowerSensor is None:
            return 0
        else:
            return self._CarPowerSensor

    @carpowersensor.setter
    def carpowersensor(self, value):
        if ex.Is_Float(value):
            self._CarPowerSensor = int(float(value))

    """Current peak"""
    @property
    def currentPeak(self) -> float:
        return max(self._CurrentPeakSensor, float(self._monthlystartpeak[datetime.now().month]))

    @currentPeak.setter
    def currentPeak(self, value):
        if ex.Is_Float(value):
            self._CurrentPeakSensor = float(value)

    """Charger enabled"""
    @property
    def ChargerEnabled(self) -> bool:
        return self._ChargerEnabled

    @ChargerEnabled.setter
    def ChargerEnabled(self, value):
        self._ChargerEnabled = True if value.lower() == "on" else False

    """Charging Done"""
    @property
    def ChargingDone(self) -> bool:
        return self._ChargingDone

    @ChargingDone.setter
    def ChargingDone(self, value):
        self._ChargingDone = True if value.lower() == "on" else False

    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        try:
            if old_state is None or old_state.state != new_state.state:
                self._UpdateSensor(entity_id, new_state.state)
        except Exception as e:
            _LOGGER.warn("Unable to handle data: ", entity_id, e)
            pass

    def _SetPowerSensors(self, powerSensorName) -> str: 
        if powerSensorName.startswith("sensor."):
            return powerSensorName
        else:
            return "sensor." + powerSensorName
    
    

    def _UpdateSensor(self,entity,value):
        if entity == self.powersensorentity:
            self.powersensor = value
            self.TotalPowerSensor.State = (self.powersensor + self.carpowersensor)
        elif entity == self.ChargerTypeData.Charger.ChargerEntity:
            self.ChargerEntity = value
        elif entity == self.ChargerTypeData.Charger.PowerMeter:
            self.carpowersensor = value
            self.TotalPowerSensor.State = (self.carpowersensor + self.powersensor)
        elif entity == self.ChargerTypeData.Charger.PowerSwitch:
            self.ChargerEntity_Switch = value
        elif entity == self.currentPeaksensorentity:
            self.currentPeak = value
        elif entity == self.TotalHourlyEnergy_Entity:
            self.TotalEnergyThisHour = value
        elif entity == self.PowerSensorMovingAverage_Entity:
            self.PowerSensorMovingAverage = value
        
        if entity in self.chargingTrackerEntities and not self.chargerblocked:
            self.Charge()
            
    def Charge(self):
        self.chargerblocked = True
        _LOGGER.error("init chargefunction")  
        if self.ChargerEnabled == True:
            _LOGGER.error("chargerenabled is true")  
            if self.ChargeController.status.name == "Start":
                _LOGGER.error("status is Start")  
                if self.ChargerEntity_Switch == "off": 
                    _LOGGER.error("switch is seen as off")
                    self.hass.services.call(self.ChargerTypeData.Charger.ServiceCalls["domain"],self.ChargerTypeData.Charger.ServiceCalls["on"],{})
                    
            elif self.ChargeController.status.name == "Stop" or self.ChargingDone == True or self.ChargeController.status.name == "Idle":
                if self.ChargerEntity_Switch == "on":   
                    self.hass.services.call(self.ChargerTypeData.Charger.ServiceCalls["domain"],self.ChargerTypeData.Charger.ServiceCalls["off"],{})       
        else:
           _LOGGER.error("chargerenabled is false")  
           if self.ChargerEntity_Switch == "on":
                self.hass.services.call(self.ChargerTypeData.Charger.ServiceCalls["domain"],self.ChargerTypeData.Charger.ServiceCalls["off"],{})
                
        self.chargerblocked = False


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
