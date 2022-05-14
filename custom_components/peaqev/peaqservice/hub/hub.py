import logging
from datetime import datetime

from homeassistant.core import (
    HomeAssistant,
)
from homeassistant.helpers.event import async_track_state_change

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import ChargeController
from custom_components.peaqev.peaqservice.hub.hubbase import HubBase
from custom_components.peaqev.peaqservice.hub.hubdata.hubdata import HubData
from custom_components.peaqev.peaqservice.prediction.prediction import Prediction
from custom_components.peaqev.peaqservice.threshold.threshold import Threshold
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class Hub(HubBase, HubData):
    """This is the hub used under normal circumstances. Ie when there is a power-meter to read from."""
    def __init__(
        self,
        hass: HomeAssistant,
        config_inputs: dict,
        domain: str
        ):
        super().__init__(hass=hass, config_inputs=config_inputs, domain=domain)
        self.create_hub_data(self.hass, config_inputs, self.domain)
        self.configpower_entity = config_inputs["powersensor"]

        """Init the subclasses"""
        self.prediction = Prediction(self)
        self.threshold = Threshold(self)
        self.chargecontroller = ChargeController(self)
        self.init_hub_values()
        trackerEntities = [
            self.chargerobject_switch.entity,
            self.configpower_entity,
            self.totalhourlyenergy.entity,
            self.currentpeak.entity
        ]

        self.chargingtracker_entities = [
            self.carpowersensor.entity,
            self.powersensormovingaverage.entity,
            self.charger_enabled.entity,
            self.charger_done.entity,
            self.chargerobject.entity,
            f"sensor.{self.domain}_{ex.nametoid(CHARGERCONTROLLER)}",
            ]

        if self.hours.price_aware is True:
            if self.hours.nordpool_entity is not None:
                self.chargingtracker_entities.append(self.hours.nordpool_entity)

        trackerEntities += self.chargingtracker_entities

        async_track_state_change(hass, trackerEntities, self.state_changed)

    def is_initialized(self) -> bool:
        ret = [self.hours.is_initialized,
               self.carpowersensor.is_initialized,
               self.chargerobject_switch.is_initialized,
               self.power.is_initialized,
               self.chargerobject.is_initialized
               ]
        return all(ret)


    @property
    def current_peak_dynamic(self):
        if self.price_aware is True and len(self.hours.dynamic_caution_hours):
            if datetime.now().hour in self.hours.dynamic_caution_hours.keys():
                return self.currentpeak.value * self.hours.dynamic_caution_hours[datetime.now().hour]
        return self.currentpeak.value

    async def _update_sensor(self, entity, value):
        if entity == self.configpower_entity:
            self.power.update(carpowersensor_value=self.carpowersensor.value, config_sensor_value=value)
        elif entity == self.carpowersensor.entity:
            self.carpowersensor.value = value
            self.power.update(carpowersensor_value=self.carpowersensor.value, config_sensor_value=None)
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
