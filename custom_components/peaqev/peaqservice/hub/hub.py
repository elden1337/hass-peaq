import logging
import time
from datetime import datetime

from homeassistant.core import (
    HomeAssistant,
)
from homeassistant.helpers.event import async_track_state_change
# from peaqevcore.hub.hub import Hub
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.services.prediction.prediction import Prediction
from peaqevcore.services.threshold.threshold import Threshold

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import ChargeController
from custom_components.peaqev.peaqservice.hub.hubbase import HubBase
from custom_components.peaqev.peaqservice.hub.hubdata.hubdata import HubData
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class HomeAssistantHub(HubBase, HubData):
    """This is the hub used under normal circumstances. Ie when there is a power-meter to read from."""
    def __init__(
        self,
        hass: HomeAssistant,
        options: HubOptions,
        domain: str,
        config_inputs: dict
        ):

        super().__init__(hass=hass, options=options, domain=domain)
        self.create_hub_data(self.hass, options, self.domain, config_inputs)
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
                return self.current_peak.value * self.dynamic_caution_hours[datetime.now().hour]
        return self.current_peak.value

    async def _update_sensor(self, entity, value):
        update_session = False

        match entity:
            case self.configpower_entity:
                self.power.update(
                    carpowersensor_value=self.carpowersensor.value,
                    config_sensor_value=value
                )
                update_session = True
            case self.carpowersensor.entity:
                self.carpowersensor.value = value
                self.power.update(
                    carpowersensor_value=self.carpowersensor.value,
                    config_sensor_value=None
                )
                update_session = True
            case self.chargerobject.entity:
                self.chargerobject.value = value
            case self.chargerobject_switch.entity:
                self.chargerobject_switch.value = value
                self.chargerobject_switch.updatecurrent()
            case self.totalhourlyenergy.entity:
                self.totalhourlyenergy.value = value
                self.current_peak.value = self.locale.data.query_model.observed_peak
                self.locale.data.query_model.try_update(
                    new_val=float(value),
                    timestamp=datetime.now()
                )
            case self.powersensormovingaverage.entity:
                self.powersensormovingaverage.value = value
            case self.powersensormovingaverage24.entity:
                self.powersensormovingaverage24.value = value
            case self.hours.nordpool_entity:
                self.hours.update_nordpool()
                update_session = True

        if self.charger.session_is_active and update_session:
            self.charger.session.session_energy = self.carpowersensor.value
            self.charger.session.session_price = float(self.hours.nordpool_value)
        if self.scheduler.schedule_created is True:
            self.scheduler.update()
        if entity in self.chargingtracker_entities and self.is_initialized is True:
            await self.charger.charge()

#
# class HomeAssistantHub(Hub):
#     hub_id = 1337
#
#     def __init__(
#         self,
#         hass: HomeAssistant,
#         config_inputs: dict,
#         domain: str
#         ):
#
#         self.domain = domain
#
#         super().__init__(
#             domain=domain,
#             state_machine=hass,
#             options= HubOptions(
#                 price_aware=config_inputs["priceaware"],
#                 peaqev_lite=config_inputs["peaqtype_is_lite"],
#                 powersensor_includes_car=config_inputs["powersensorincludescar"],
#                 locale=config_inputs["locale"],
#                 chargertype=config_inputs["chargertype"],
#                 chargerid=config_inputs["chargerid"],
#                 startpeaks=config_inputs["startpeaks"]
#                 )
#             )
#         self.configpower_entity = config_inputs["powersensor"]
#
#         self.init_hub_values()
#         trackerEntities = [
#             self.configpower_entity,
#             self.sensors.totalhourlyenergy.entity
#         ]
#
#         self.chargingtracker_entities = [
#             self.sensors.chargerobject_switch.entity,
#             self.sensors.carpowersensor.entity,
#             self.sensors.powersensormovingaverage.entity,
#             self.sensors.powersensormovingaverage24.entity,
#             self.sensors.charger_enabled.entity,
#             self.sensors.charger_done.entity,
#             self.sensors.chargerobject.entity,
#             f"sensor.{self.domain}_{ex.nametoid(CHARGERCONTROLLER)}",
#             ]
#
#         if self.hours.price_aware is True:
#             if self.hours.nordpool_entity is not None:
#                 self.chargingtracker_entities.append(self.hours.nordpool_entity)
#
#         trackerEntities += self.chargingtracker_entities
#         async_track_state_change(hass, trackerEntities, self.state_changed)
#
#     initialized_log_last_logged = 0
#     not_ready_list_old_state = 0
#
#     @property
#     def non_hours(self) -> list:
#         return self.scheduler.non_hours if self.scheduler.scheduler_active else self.hours.non_hours
#
#     @property
#     def dynamic_caution_hours(self) -> dict:
#         return self.scheduler.caution_hours if self.scheduler.scheduler_active else self.hours.dynamic_caution_hours
#
#     @callback
#     async def state_changed(self, entity_id, old_state, new_state):
#         try:
#             if old_state is None or old_state.state != new_state.state:
#                 await self._update_sensor(entity_id, new_state.state)
#         except Exception as e:
#             msg = f"Unable to handle data: {entity_id} ({e})"
#             _LOGGER.error(msg)
#
#     async def call_enable_peaq(self):
#         """peaqev.enable"""
#         self.sensors.charger_enabled.value = True
#         self.sensors.charger_done.value = False
#
#     async def call_disable_peaq(self):
#         """peaqev.disable"""
#         self.sensors.charger_enabled.value = False
#         self.sensors.charger_done.value = False
#
#     async def call_override_nonhours(self, hours: int = 1):
#         """peaqev.override_nonhours"""
#         self.timer.update(hours)
#
#     async def call_schedule_needed_charge(
#             self,
#             charge_amount: float,
#             departure_time: str,
#             schedule_starttime: str = None,
#             override_settings: bool = False
#     ):
#         dep_time = datetime.strptime(departure_time, '%y-%m-%d %H:%M')
#         if schedule_starttime is not None:
#             start_time = datetime.strptime(schedule_starttime, '%y-%m-%d %H:%M')
#         else:
#             start_time = datetime.now()
#         _LOGGER.debug(f"scheduler params. charge: {charge_amount}, dep-time: {dep_time}, start_time: {start_time}")
#         self.scheduler.create_schedule(charge_amount, dep_time, start_time, override_settings)
#         self.scheduler.update()
#
#     async def call_scheduler_cancel(self):
#         self.scheduler.cancel()
#
#     @property
#     def is_initialized(self) -> bool:
#         ret = {"hours": self.hours.is_initialized,
#                "carpowersensor": self.sensors.carpowersensor.is_initialized,
#                "chargerobject_switch": self.sensors.chargerobject_switch.is_initialized,
#                "power": self.sensors.power.is_initialized,
#                "chargerobject": self.sensors.chargerobject.is_initialized
#                }
#
#         if all(ret.values()):
#             return True
#         not_ready = []
#         for r in ret:
#             if ret[r] is False:
#                 not_ready.append(r)
#         if len(not_ready) != self.not_ready_list_old_state or self.initialized_log_last_logged - time.time() > 30:
#             _LOGGER.warning(f"{not_ready} has not initialized yet.")
#             self.not_ready_list_old_state = len(not_ready)
#             self.initialized_log_last_logged = time.time()
#         if "chargerobject" in not_ready:
#             self.chargertype.charger.getentities()
#         return False
#
#     @property
#     def current_peak_dynamic(self):
#         if self.options.price_aware is True and len(self.dynamic_caution_hours):
#             if datetime.now().hour in self.dynamic_caution_hours.keys() and self.timer.is_override is False:
#                 return self.sensors.current_peak.value * self.dynamic_caution_hours[datetime.now().hour]
#         return self.sensors.current_peak.value
#
#     async def _update_sensor(self, entity, value):
#         update_session = False
#
#         match entity:
#             case self.configpower_entity:
#                 self.power.update(
#                     carpowersensor_value=self.carpowersensor.value,
#                     config_sensor_value=value
#                 )
#                 update_session = True
#             case self.carpowersensor.entity:
#                 self.carpowersensor.value = value
#                 self.power.update(
#                     carpowersensor_value=self.carpowersensor.value,
#                     config_sensor_value=None
#                 )
#                 update_session = True
#             case self.chargerobject.entity:
#                 self.chargerobject.value = value
#             case self.chargerobject_switch.entity:
#                 self.chargerobject_switch.value = value
#                 self.chargerobject_switch.updatecurrent()
#             case self.totalhourlyenergy.entity:
#                 self.totalhourlyenergy.value = value
#                 self.current_peak.value = self.locale.data.query_model.observed_peak
#                 self.locale.data.query_model.try_update(
#                     new_val=float(value),
#                     timestamp=datetime.now()
#                 )
#             case self.powersensormovingaverage.entity:
#                 self.powersensormovingaverage.value = value
#             case self.powersensormovingaverage24.entity:
#                 self.powersensormovingaverage24.value = value
#             case self.hours.nordpool_entity:
#                 self.hours.update_nordpool()
#                 update_session = True
#
#         if self.charger.session_is_active and update_session:
#             self.charger.session.session_energy = self.carpowersensor.value
#             self.charger.session.session_price = float(self.hours.nordpool_value)
#         if self.scheduler.schedule_created is True:
#             self.scheduler.update()
#         if entity in self.chargingtracker_entities and self.is_initialized is True:
#             await self.charger.charge()
#
#     def init_hub_values(self):
#         """Initialize values from Home Assistant on the set objects"""
#         self.chargerobject.value = self.hass.states.get(self.chargerobject.entity).state if self.hass.states.get(
#             self.chargerobject.entity) is not None else 0
#         self.chargerobject_switch.value = self.hass.states.get(
#             self.chargerobject_switch.entity).state if self.hass.states.get(
#             self.chargerobject_switch.entity) is not None else ""
#         self.chargerobject_switch.updatecurrent()
#         self.carpowersensor.value = self.hass.states.get(self.carpowersensor.entity).state if self.hass.states.get(
#             self.carpowersensor.entity) is not None else 0
#         self.totalhourlyenergy.value = self.hass.states.get(self.totalhourlyenergy.entity) if self.hass.states.get(
#             self.totalhourlyenergy.entity) is not None else 0