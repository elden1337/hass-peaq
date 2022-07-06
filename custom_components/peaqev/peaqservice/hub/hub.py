import logging
import time
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
            self.configpower_entity,
            self.totalhourlyenergy.entity
        ]

        self.chargingtracker_entities = [
            self.chargerobject_switch.entity,
            self.carpowersensor.entity,
            self.powersensormovingaverage.entity,
            self.powersensormovingaverage24.entity,
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


    initialized_log_last_logged = 0
    not_ready_list_old_state = 0

    @property
    def is_initialized(self) -> bool:
        ret = {"hours": self.hours.is_initialized,
               "carpowersensor": self.carpowersensor.is_initialized,
               "chargerobject_switch": self.chargerobject_switch.is_initialized,
               "power": self.power.is_initialized,
               "chargerobject": self.chargerobject.is_initialized
               }

        if all(ret.values()):
            return True
        not_ready = []
        for r in ret:
            if ret[r] is False:
                not_ready.append(r)
        if len(not_ready) != self.not_ready_list_old_state or self.initialized_log_last_logged - time.time() > 30:
            _LOGGER.warning(f"{not_ready} has not initialized yet.")
            self.not_ready_list_old_state = len(not_ready)
            self.initialized_log_last_logged = time.time()
        if "chargerobject" in not_ready:
            self.chargertype.charger.getentities()
        return False

    @property
    def current_peak_dynamic(self):
        if self.price_aware is True and len(self.dynamic_caution_hours):
            if datetime.now().hour in self.dynamic_caution_hours.keys() and self.timer.is_override is False:
                return self.currentpeak.value * self.dynamic_caution_hours[datetime.now().hour]
        return self.currentpeak.value

    async def _update_sensor(self, entity, value):
        if entity == self.configpower_entity:
            self.power.update(carpowersensor_value=self.carpowersensor.value, config_sensor_value=value)
        elif entity == self.carpowersensor.entity:
            self.carpowersensor.value = value
            self.power.update(carpowersensor_value=self.carpowersensor.value, config_sensor_value=None)
            if self.charger.session_is_active:
                self.charger.session.session_energy = value
        elif entity == self.chargerobject.entity:
            self.chargerobject.value = value
        elif entity == self.chargerobject_switch.entity:
            self.chargerobject_switch.value = value
            self.chargerobject_switch.updatecurrent()
        elif entity == self.totalhourlyenergy.entity:
            self.totalhourlyenergy.value = value
            self.currentpeak.value = self.locale.data.query_model.observed_peak
            self.locale.data.query_model.try_update(float(value))
        elif entity == self.powersensormovingaverage.entity:
            self.powersensormovingaverage.value = value
        elif entity == self.powersensormovingaverage24.entity:
            self.powersensormovingaverage24.value = value
        elif entity == self.hours.nordpool_entity:
            self.hours.update_nordpool()
        if entity in self.chargingtracker_entities and self.is_initialized is True:
            await self.charger.charge()
        if self.scheduler.schedule_created is True:
            self.scheduler.update()
