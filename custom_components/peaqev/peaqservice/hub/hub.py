import logging
from datetime import datetime

from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.helpers.event import async_track_state_change

import custom_components.peaqev.peaqservice.util.constants as constants
import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.chargecontroller import ChargeController
from custom_components.peaqev.peaqservice.charger import Charger
from custom_components.peaqev.peaqservice.hourselection import (PriceAwareHours, RegularHours)
from custom_components.peaqev.peaqservice.chargertypes.chargertypes import ChargerTypeData
from custom_components.peaqev.peaqservice.hub.power import Power
from custom_components.peaqev.peaqservice.localetypes.locale import LocaleData
from custom_components.peaqev.peaqservice.prediction import Prediction
from custom_components.peaqev.peaqservice.threshold import Threshold
from custom_components.peaqev.peaqservice.hub.hubmember import (
    HubMember,
    CurrentPeak,
    ChargerSwitch
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
        self.locale = LocaleData(config_inputs["locale"], self.domain)
        self.chargertype = ChargerTypeData(hass, config_inputs["chargertype"], config_inputs["chargerid"])
        self._powersensor_includes_car = bool(config_inputs["powersensorincludescar"])
        #self._monthlystartpeak = config_inputs["startpeaks"]

        if config_inputs["priceaware"] is True:
            self.hours = PriceAwareHours(
                hass=self.hass,
                price_aware=config_inputs["priceaware"],
                absolute_top_price=config_inputs["absolute_top_price"],
                non_hours=config_inputs["nonhours"],
                caution_hours=config_inputs["cautionhours"],
                cautionhour_type=config_inputs["cautionhour_type"]
            )
        else:
            self.hours = RegularHours(
                non_hours=config_inputs["nonhours"],
                caution_hours=config_inputs["cautionhours"]
            )



        self.charger_enabled = HubMember(
            type=bool,
            listenerentity=f"binary_sensor.{self.domain}_{ex.nametoid(constants.CHARGERENABLED)}",
            initval=False
        )
        self.powersensormovingaverage = HubMember(
            type=int,
            listenerentity=f"sensor.{self.domain}_{ex.nametoid(constants.AVERAGECONSUMPTION)}",
            initval=0
        )
        self.totalhourlyenergy = HubMember(
            type=float,
            listenerentity=f"sensor.{self.domain}_{ex.nametoid(constants.CONSUMPTION_TOTAL_NAME)}_{constants.HOURLY}",
            initval=0
        )
        self.charger_done = HubMember(
            type=bool,
            listenerentity=f"binary_sensor.{self.domain}_{ex.nametoid(constants.CHARGERDONE)}",
            initval=False
        )

        self.power = Power(
            configsensor=config_inputs["powersensor"],
            powersensor_includes_car=self._powersensor_includes_car
        )

        self.configpower_entity = config_inputs["powersensor"]

        self.carpowersensor = HubMember(
            type=int,
            listenerentity=self.chargertype.charger.powermeter,
            initval=0
        )

        self.currentpeak = CurrentPeak(
            type=float,
            listenerentity=self.locale.current_peak_entity,
            initval=0,
            startpeaks=config_inputs["startpeaks"]
        )
        self.chargerobject = HubMember(
            type=str,
            listenerentity=self.chargertype.charger.chargerentity
        )
        self.chargerobject_switch = ChargerSwitch(
            hass=self.hass,
            type=bool,
            listenerentity=self.chargertype.charger.powerswitch,
            initval=False,
            currentname=self.chargertype.charger.ampmeter,
            ampmeter_is_attribute=self.chargertype.charger.ampmeter_is_attribute
        )

        """Init the subclasses"""
        self.prediction = Prediction(self)
        self.threshold = Threshold(self)
        self.chargecontroller = ChargeController(self)
        self.charger = Charger(
            self,
            hass,
            self.chargertype.charger.servicecalls
        )
        
        self.init_hub_values()
        
        trackerEntities = [
            self.carpowersensor.entity,
            self.chargerobject_switch.entity,
            self.configpower_entity,
            self.totalhourlyenergy.entity,
            self.currentpeak.entity
        ]

        self.chargingtracker_entities = [
            self.powersensormovingaverage.entity, 
            self.charger_enabled.entity, 
            self.charger_done.entity, 
            self.chargerobject.entity,
            f"sensor.{self.domain}_{ex.nametoid(constants.CHARGERCONTROLLER)}",
            ]

        if self.hours.price_aware is True:
            if self.hours.nordpool_entity is not None:
                self.chargingtracker_entities.append(self.hours.nordpool_entity)

        trackerEntities += self.chargingtracker_entities
        
        async_track_state_change(hass, trackerEntities, self.state_changed)
 
    def init_hub_values(self):
        """Initialize values from Home Assistant on the set objects"""
        self.chargerobject.value = self.hass.states.get(self.chargerobject.entity).state if self.hass.states.get(self.chargerobject.entity) is not None else 0
        self.chargerobject_switch.value = self.hass.states.get(self.chargerobject_switch.entity).state if self.hass.states.get(self.chargerobject_switch.entity) is not None else ""
        self.chargerobject_switch.updatecurrent()
        self.carpowersensor.value = self.hass.states.get(self.carpowersensor.entity).state if self.hass.states.get(self.carpowersensor.entity) is not None else 0
        self.totalhourlyenergy.value = self.hass.states.get(self.totalhourlyenergy.entity) if self.hass.states.get(self.totalhourlyenergy.entity) is not None else 0
        self.currentpeak.value = self.hass.states.get(self.currentpeak.entity) if self.hass.states.get(self.currentpeak.entity) is not None else 0

    async def is_initialized(self) -> bool:
        return True

    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        try:
            if old_state is None or old_state.state != new_state.state:
                await self._updatesensor(entity_id, new_state.state)
        except Exception as e:
            _LOGGER.warn("Unable to handle data: ", entity_id, e)
            pass

    async def _updatesensor(self, entity, value):
        if entity == self.configpower_entity:
            self.power.update(carpowersensor_value=self.carpowersensor.value, val=value)
        elif entity == self.carpowersensor.entity:
            self.carpowersensor.value = value
            self.power.update(carpowersensor_value=value, val=None)
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
        elif entity == self.hours.nordpool_entity:
            self.hours.update_nordpool()
        
        if entity in self.chargingtracker_entities:
            await self.charger.charge()

    """Methods called from servicecalls"""
    async def call_enable_peaq(self):
        """peaqev.enable"""
        self.charger_enabled.value = True
        self.charger_done.value = False

    async def call_disable_peaq(self):
        """peaqev.disable"""
        self.charger_enabled.value = False
        self.charger_done.value = False
