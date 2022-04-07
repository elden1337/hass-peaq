import logging
from datetime import datetime

import custom_components.peaqev.peaqservice.extensionmethods as ex
import custom_components.peaqev.peaqservice.constants as constants
from custom_components.peaqev.peaqservice.chargecontroller import ChargeController
from custom_components.peaqev.peaqservice.prediction import Prediction
from custom_components.peaqev.peaqservice.threshold import Threshold
from custom_components.peaqev.peaqservice.locale import LocaleData
from custom_components.peaqev.peaqservice.charger import Charger
from custom_components.peaqev.peaqservice.util.hubmember import (
    HubMember,
    CurrentPeak,
    ChargerSwitch
)
from custom_components.peaqev.peaqservice.chargertypes import ChargerTypeData
from custom_components.peaqev.sensors.peaqsqlsensor import PeaqSQLSensorHelper
from homeassistant.helpers.event import async_track_state_change
from homeassistant.core import (
    HomeAssistant,
    callback,
)

_LOGGER = logging.getLogger(__name__)

class Hub:
    hub_id = 1337
    
    def __init__(
        self, 
        hass: HomeAssistant, 
        config_inputs: dict,
        domain: str
        ):
        self.hass = hass
        self.hubname = domain.capitalize()
        self.domain = domain

        """from the config inputs"""
        self.localedata = LocaleData(config_inputs["locale"])
        self.chargertypedata = ChargerTypeData(hass, config_inputs["chargertype"], config_inputs["chargerid"])
        self._powersensor_includes_car = config_inputs["powersensorincludescar"]
        self._monthlystartpeak = config_inputs["monthlystartpeak"]
        self.nonhours = config_inputs["nonhours"]
        self.cautionhours = config_inputs["cautionhours"]
        self.powersensor = HubMember(int, config_inputs["powersensor"], 0)

        self.charger_enabled = HubMember(bool, f"binary_sensor.{self.domain}_{ex.nametoid(constants.CHARGERENABLED)}", False)
        self.powersensormovingaverage = HubMember(int, f"sensor.{self.domain}_{ex.nametoid(constants.AVERAGECONSUMPTION)}", 0)
        self.totalhourlyenergy = HubMember(float, f"sensor.{self.domain}_{ex.nametoid(constants.CONSUMPTION_TOTAL_NAME)}_{constants.HOURLY}", 0)
        self.charger_done = HubMember(bool, f"binary_sensor.{self.domain}_{ex.nametoid(constants.CHARGERDONE)}", False)
        self.totalpowersensor = HubMember(int, name = constants.TOTALPOWER)
        self.carpowersensor = HubMember(int, self.chargertypedata.charger.powermeter, 0) 
        self.currentpeak = CurrentPeak(float, f"sensor.{self.domain}_{ex.nametoid(PeaqSQLSensorHelper('').getquerytype(self.localedata.observedpeak)['name'])}", 0, self._monthlystartpeak[str(datetime.now().month)])
        self.chargerobject = HubMember(str, self.chargertypedata.charger.chargerentity)
        self.chargerobject_switch = ChargerSwitch(self.hass, str, self.chargertypedata.charger.powerswitch, False, self.chargertypedata.charger.ampmeter, self.chargertypedata.charger.ampmeter_is_attribute)

        """Init the subclasses"""
        self.prediction = Prediction(self)
        self.threshold = Threshold(self)
        self.chargecontroller = ChargeController(self)
        self.charger = Charger(self, hass, self.chargertypedata.charger.servicecalls)
        
        self.init_hub_values()
        
        trackerEntities = [
            self.carpowersensor.entity,
            self.chargerobject_switch.entity,
            self.powersensor.entity,
            self.totalhourlyenergy.entity,
            self.currentpeak.entity
        ]

        self.chargingtracker_entities = [
            self.powersensormovingaverage.entity, 
            self.charger_enabled.entity, 
            self.charger_done.entity, 
            self.chargerobject.entity,
            f"sensor.{self.domain}_{ex.nametoid(constants.CHARGERCONTROLLER)}"
            ]

        trackerEntities += self.chargingtracker_entities
        
        async_track_state_change(hass, trackerEntities, self.state_changed)
 
    def init_hub_values(self):
        """Initialize values from Home Assistant on the set objects"""

        self.chargerobject.value = self.hass.states.get(self.chargerobject.entity)
        self.chargerobject_switch.value = self.hass.states.get(self.chargerobject_switch.entity)
        self.chargerobject_switch.updatecurrent()
        self.carpowersensor.value = self.hass.states.get(self.carpowersensor.entity)
        self.totalhourlyenergy.value = self.hass.states.get(self.totalhourlyenergy.entity)
        self.currentpeak.value = self.hass.states.get(self.currentpeak.entity)
       
    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        try:
            if old_state is None or old_state.state != new_state.state:
                await self._updatesensor(entity_id, new_state.state)
        except Exception as e:
            _LOGGER.warn("Unable to handle data: ", entity_id, e)
            pass

    async def _updatesensor(self, entity, value):
        if entity == self.powersensor.entity:
            if not self._powersensor_includes_car:
                self.powersensor.value = value
                self.totalpowersensor.value = (self.powersensor.value + self.carpowersensor.value)
            else:
                self.totalpowersensor.value = value
                self.powersensor.value = (self.totalpowersensor.value - self.carpowersensor.value)
        elif entity == self.carpowersensor.entity:
            self.carpowersensor.value = value
            if not self._powersensor_includes_car:
                self.totalpowersensor.value = (self.carpowersensor.value + self.powersensor.value)
            else:
                self.powersensor.value = (self.totalpowersensor.value - self.carpowersensor.value)
        elif entity == self.chargerobject.entity:
            self.chargerobject.value = value
        elif entity == self.chargerobject_switch.entity:
            self.chargerobject_switch.value = value
            self.chargerobject_switch.updatecurrent()
        elif entity == self.currentpeak.entity:
            self.currentpeak.value = value
        elif entity == self.totalhourlyenergy.entity:
            self.totalhourlyenergy.value = value
        elif entity == self.powersensormovingaverage.entity:
            self.powersensormovingaverage.value = value
        
        if entity in self.chargingtracker_entities:
            await self.charger.charge()
