from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from homeassistant.core import (
    HomeAssistant,
    callback
)
from homeassistant.helpers.event import async_track_state_change
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.services.hourselection.initializers.hoursbase import Hours
from peaqevcore.services.prediction.prediction import Prediction
from peaqevcore.services.scheduler.scheduler import SchedulerFacade
from peaqevcore.services.timer.timer import Timer

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.charger.charger import Charger
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.gainloss.gain_loss import GainLoss
from custom_components.peaqev.peaqservice.hub.factories.chargecontroller_factory import ChargeControllerFactory
from custom_components.peaqev.peaqservice.hub.factories.chargertype_factory import ChargerTypeFactory
from custom_components.peaqev.peaqservice.hub.factories.hourselection_factory import HourselectionFactory
from custom_components.peaqev.peaqservice.hub.factories.hubsensors_factory import HubSensorsFactory
from custom_components.peaqev.peaqservice.hub.factories.state_changes_factory import StateChangesFactory
from custom_components.peaqev.peaqservice.hub.factories.threshold_factory import ThresholdFactory
from custom_components.peaqev.peaqservice.hub.hub_initializer import HubInitializer
from custom_components.peaqev.peaqservice.hub.nordpool.nordpool import NordPoolUpdater
from custom_components.peaqev.peaqservice.hub.observer import Observer
from custom_components.peaqev.peaqservice.hub.servicecalls import ServiceCalls
from custom_components.peaqev.peaqservice.power_canary.power_canary import PowerCanary
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class HomeAssistantHub:
    hub_id = 1337

    def __init__(
            self,
            hass: HomeAssistant,
            options: HubOptions,
            domain: str
    ):
        self.state_machine = hass
        self.domain = domain
        self.options: HubOptions = options
        self._is_initialized = False
        self.observer = Observer(self)
        self.hubname = domain.capitalize()

        self.chargertype = ChargerTypeFactory.create(
            hass=hass,
            input_type=self.options.charger.chargertype,
            options=self.options
        ) #charger?
        self.charger = Charger(hub=self, chargertype=self.chargertype) #top level
        
        self.sensors = HubSensorsFactory.create(self.options) #top level
        self.timer: Timer = Timer()
        self.hours: Hours = HourselectionFactory.create(self) #top level
        self.threshold = ThresholdFactory.create(self) #top level
        self.prediction = Prediction(self) #threshold
        self.scheduler = SchedulerFacade(hub=self, options=self.hours.options) #hours

        self.sensors.setup(state_machine=hass, options=options, domain=domain, chargerobject=self.chargertype)
        self.sensors.init_hub_values()

        self.servicecalls = ServiceCalls(self) #top level
        self.states = StateChangesFactory.create(self) #top level
        self.chargecontroller = ChargeControllerFactory.create(self, charger_states=self.chargertype.chargerstates) #charger
        self.nordpool = NordPoolUpdater(hub=self, is_active=self.hours.price_aware) #hours
        self.power_canary = PowerCanary(hub=self)  #power
        self.initializer = HubInitializer(self) #top level
        self.gainloss = GainLoss(self) #power

        tracker_entities = []

        if not options.peaqev_lite:
            tracker_entities.append(self.options.powersensor)
            tracker_entities.append(self.sensors.totalhourlyenergy.entity)

        # self.coordinator = self._set_coordinator()
        self._set_observers()

        self.chargingtracker_entities = self._set_chargingtracker_entities()
        tracker_entities += self.chargingtracker_entities
        async_track_state_change(hass, tracker_entities, self.state_changed)

    @property
    def enabled(self) -> bool:
        return self.sensors.charger_enabled.value

    @property
    def non_hours(self) -> list:
        if self.scheduler.scheduler_active:
            return self.scheduler.non_hours
        return self.hours.non_hours

    @property
    def dynamic_caution_hours(self) -> dict:
        if self.scheduler.scheduler_active:
            return self.scheduler.caution_hours
        return self.hours.dynamic_caution_hours

    @property
    def current_peak_dynamic(self):
        """Dynamically calculated peak to adhere to caution-hours"""
        if self.options.price.price_aware and len(self.dynamic_caution_hours) > 0:
            if datetime.now().hour in self.dynamic_caution_hours.keys() and not self.timer.is_override:
                return self.sensors.current_peak.value * self.dynamic_caution_hours[datetime.now().hour]
        return self.sensors.current_peak.value

    @property
    def is_initialized(self) -> bool:
        if hasattr(self, "initializer"):
            if self.initializer.check():
                del self.initializer
                self.observer.activate()
                return True
            return False
        return True

    def _set_chargingtracker_entities(self) -> list:
        ret = [f"sensor.{self.domain}_{ex.nametoid(CHARGERCONTROLLER)}"]
        if hasattr(self.sensors, "chargerobject_switch"):
            ret.append(self.sensors.chargerobject_switch.entity)
        if hasattr(self.sensors, "carpowersensor"):
            ret.append(self.sensors.carpowersensor.entity)
        if hasattr(self.sensors, "charger_enabled"):
            ret.append(self.sensors.charger_enabled.entity)
        if hasattr(self.sensors, "charger_done"):
            ret.append(self.sensors.charger_done.entity)

        if self.chargertype.type not in [ChargerType.Outlet, ChargerType.NoCharger]:
            ret.append(self.sensors.chargerobject.entity)
        if not self.options.peaqev_lite:
            ret.append(self.sensors.powersensormovingaverage.entity)
            ret.append(self.sensors.powersensormovingaverage24.entity)
        if self.hours.nordpool_entity is not None:
            ret.append(self.hours.nordpool_entity)
        return ret

    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        if entity_id is not None:
            try:
                if old_state is None or old_state != new_state:
                    await self.states.update_sensor(entity_id, new_state.state)
            except Exception as e:
                msg = f"Unable to handle data-update: {entity_id} {old_state}|{new_state}. Exception: {e}"
                _LOGGER.error(msg)

    @property
    def watt_cost(self) -> int:
        if self.options.price.price_aware:
            try:
                return int(round(float(self.sensors.power.total.value) * float(self.nordpool.state), 0))
            except:
                return 0
        return 0

    """Composition below here"""
    def get_power_sensor_from_hass(self) -> float|None:
        ret = self.state_machine.states.get(self.options.powersensor)
        if ret is not None:
            try:
                return float(ret.state)
            except:
                return None
        return ret

    def get_chargerobject_value(self) -> str:
        ret = getattr(self.sensors.chargerobject, "value", "unknown")
        return ret.lower()

    def set_chargerobject_value(self, value) -> None:
        if hasattr(self.sensors, "chargerobject"):
            self.sensors.chargerobject.value = value

    @property
    def prices(self) -> list:
        if self.options.price.price_aware:
            return self.hours.prices
        return []

    @prices.setter
    def prices(self, val) -> None:
        if self.options.price.price_aware:
            if self.hours.prices != val:
                _LOGGER.debug(f"setting today's prices with: {val}")
                self.hours.prices = val

    @property
    def prices_tomorrow(self) -> list:
        if self.options.price.price_aware:
            return self.hours.prices_tomorrow
        return []

    @prices_tomorrow.setter
    def prices_tomorrow(self, val) -> None:
        if self.options.price.price_aware:
            if self.hours.prices_tomorrow != val:
                _LOGGER.debug(f"setting tomorrow's prices with: {val}")
                self.hours.prices_tomorrow = val

    @property
    def is_free_charge(self) -> bool:
        if hasattr(self.sensors, "locale"):
            return self.sensors.locale.data.free_charge(self.sensors.locale.data)
        return False

    def _update_prices(self, prices: list) -> None:
        self.prices = prices[0]
        self.prices_tomorrow = prices[1]

    def _update_average_monthly_price(self, val) -> None:
        if self.options.price.price_aware and isinstance(val, float):
            self.hours.update_top_price(val)

    def _update_average_weekly_price(self, val) -> None:
        if self.options.price.price_aware and isinstance(val, float):
            self.hours.adjusted_average = val

    @property
    def charger_done(self) -> bool:
        if hasattr(self.sensors, "charger_done"):
            return self.sensors.charger_done.value
        return False

    def _update_charger_done(self, val):
        if hasattr(self.sensors, "charger_done"):
            self.sensors.charger_done.value = bool(val)

    def _update_charger_enabled(self, val):
        if hasattr(self.sensors, "charger_enabled"):
            self.sensors.charger_enabled.value = bool(val)
        else:
            raise Exception("Peaqev cannot function without a charger_enabled entity")

    # async def get_states_async(self, module) -> dict:
    #     if module in self.coordinator.keys():
    #         return self.coordinator.get(module)
    #     return {}

    # def get_states(self, module) -> dict:
    #     return asyncio.run_coroutine_threadsafe(
    #         self.get_states_async(module), self.state_machine.loop
    #     ).result()

    # def _set_coordinator(self) -> dict:
    #     ret = {}
    #     chargecontroller = {
    #         "status":         self.chargecontroller.status_type,
    #         "status_string":  self.chargecontroller.status_string,
    #         "is_initialized": self.chargecontroller.is_initialized}
    #     ret["chargecontroller"] = chargecontroller
    #     return ret

    def _set_observers(self) -> None:
        self.observer.add("prices changed", self._update_prices)
        self.observer.add("monthly average price changed", self._update_average_monthly_price)
        self.observer.add("weekly average price changed", self._update_average_weekly_price)
        self.observer.add("update charger done", self._update_charger_done)
        self.observer.add("update charger enabled", self._update_charger_enabled)
