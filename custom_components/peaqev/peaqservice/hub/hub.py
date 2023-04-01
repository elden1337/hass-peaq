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
from peaqevcore.hub.hub_sensors import IHubSensors
from peaqevcore.services.chargertype.chargertype_base import ChargerBase
from peaqevcore.services.hourselection.initializers.hoursbase import Hours
from peaqevcore.services.prediction.prediction import Prediction
from peaqevcore.services.scheduler.scheduler import SchedulerFacade
from peaqevcore.services.threshold.thresholdbase import ThresholdBase
from peaqevcore.services.timer.timer import Timer

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import IChargeController
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
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import IStateChanges
from custom_components.peaqev.peaqservice.power_canary.power_canary import PowerCanary
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class HomeAssistantHub:
    hub_id = 1337
    chargertype: ChargerBase
    charger: Charger
    sensors: IHubSensors
    timer: Timer
    hours: Hours
    threshold: ThresholdBase
    prediction: Prediction
    scheduler: SchedulerFacade
    servicecalls: ServiceCalls
    states: IStateChanges
    chargecontroller: IChargeController
    nordpool: NordPoolUpdater
    power_canary: PowerCanary
    gainloss: GainLoss

    def __init__(
            self,
            hass: HomeAssistant,
            options: HubOptions,
            domain: str
    ):
        self._lock = asyncio.Lock()
        self.hubname = domain.capitalize()
        self.state_machine = hass
        self.domain = domain
        self.options: HubOptions = options
        self._is_initialized = False
        self.observer = Observer(self)
        self._set_observers()
        self.initializer = HubInitializer(self)

    async def setup(self):
        self.chargertype = await self.state_machine.async_add_executor_job(ChargerTypeFactory.create,
                                                                           self.state_machine,
                                                                           self.options.charger.chargertype,
                                                                           self.options)  # charger?
        self.charger = Charger(hub=self, chargertype=self.chargertype)  # top level
        self.sensors: IHubSensors = await HubSensorsFactory.create(self.options)  # top level
        self.timer: Timer = Timer()
        self.hours: Hours = await HourselectionFactory.create(self)  # top level
        self.threshold: ThresholdBase = await ThresholdFactory.create(self)  # top level
        self.prediction = Prediction(self)  # threshold
        self.scheduler = SchedulerFacade(hub=self, options=self.hours.options)  # hours

        self.sensors.setup(state_machine=self.state_machine, options=self.options, domain=self.domain,
                           chargerobject=self.chargertype)
        self.sensors.init_hub_values()
        self.servicecalls = ServiceCalls(self)  # top level
        self.states = await StateChangesFactory.create(self)  # top level
        self.chargecontroller: IChargeController = await ChargeControllerFactory.create(self, charger_states=self.chargertype.chargerstates)  # charger
        self.nordpool = NordPoolUpdater(hub=self, is_active=self.hours.price_aware)  # hours
        self.power_canary = PowerCanary(hub=self)  # power
        self.gainloss = GainLoss(self)  # power

        self.chargingtracker_entities = []
        trackers = await self.async_setup_tracking()
        async_track_state_change(self.state_machine, trackers, self.async_state_changed)

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
                self.observer.broadcast("hub initialized")
                return True
            return False
        return True

    @property
    def watt_cost(self) -> int:
        if self.options.price.price_aware:
            try:
                return int(round(float(self.sensors.power.total.value) * float(self.nordpool.state), 0))
            except:
                return 0
        return 0

    @callback
    async def async_state_changed(self, entity_id, old_state, new_state):
        #async with self._lock:
            if entity_id is not None:
                try:
                    if old_state is None or old_state != new_state:
                        await self.states.async_update_sensor(entity_id, new_state.state)
                except Exception as e:
                    msg = f"Unable to handle data-update: {entity_id} {old_state}|{new_state}. Exception: {e}"
                    _LOGGER.error(msg)

    async def async_setup_tracking(self) -> list:
        tracker_entities = []
        if not self.options.peaqev_lite:
            tracker_entities.append(self.options.powersensor)
            tracker_entities.append(self.sensors.totalhourlyenergy.entity)
        self.chargingtracker_entities = await self.async_set_chargingtracker_entities()
        tracker_entities += self.chargingtracker_entities
        return tracker_entities

    async def async_set_chargingtracker_entities(self) -> list:
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

    def _set_observers(self) -> None:
        self.observer.add("prices changed", self._update_prices)
        self.observer.add("monthly average price changed", self._update_average_monthly_price)
        self.observer.add("weekly average price changed", self._update_average_weekly_price)
        self.observer.add("update charger done", self.async_update_charger_done, _async=True)
        self.observer.add("update charger enabled", self.async_update_charger_enabled, _async=True)


    """Composition below here"""

    async def async_set_init_dict(self, init_dict):
        ret = await self.sensors.locale.data.query_model.peaks.async_set_init_dict(init_dict)
        if ret:
            ff = getattr(self.sensors.locale.data.query_model.peaks, "export_peaks")
            _LOGGER.debug(f"intialized_peaks: {ff}")

    def get_power_sensor_from_hass(self) -> float | None:
        ret = self.state_machine.states.get(self.options.powersensor)
        if ret is not None:
            try:
                return float(ret.state)
            except:
                return None
        return ret

    async def async_get_chargerobject_value(self) -> str:
        ret = await self.async_request_sensor_data("chargerobject_value")[0]
        return ret.lower()

    async def async_set_chargerobject_value(self, value) -> None:
        if hasattr(self.sensors, "chargerobject"):
            setattr(self.sensors.chargerobject, "value", value)

    async def async_request_sensor_data(self, *args) -> dict:
        lookup = {
        "chargerobject_value": getattr(self.sensors.chargerobject, "value", "unknown"),
        "prices_tomorrow": getattr(self.hours, "prices_tomorrow"),
        "non_hours": getattr(self.hours, "non_hours"),
        "caution_hours": getattr(self.hours, "dynamic_caution_hours"),
        "state": getattr(self.chargecontroller, "state_display_model"), #todo: fix this, cant be called state and should not be spawned from chargecontroller.
        "currency": getattr(self.nordpool, "currency"),
        "offsets": getattr(self.hours, "offsets", {}),
        "average_nordpool_data": getattr(self.nordpool, "average_data"),
        "use_cent": getattr(self.nordpool.model, "use_cent"),
        "current_peak": getattr(self.sensors.current_peak, "value"),
        "avg_kwh_price": await self.state_machine.async_add_executor_job(self.hours.get_average_kwh_price),
        "max_charge": await self.state_machine.async_add_executor_job(self.hours.get_total_charge),
        "average_weekly": getattr(self.nordpool, "average_weekly"),
        "average_monthly": getattr(self.nordpool, "average_month"),
        }
        ret = {}
        for arg in args:
            ret[arg] = lookup.get(arg, None)
        return ret

    async def async_get_money_sensor_data(self) -> dict | None:
        ret = {}
        ret["prices_tomorrow"] = getattr(self.hours, "prices_tomorrow")
        ret["non_hours"] = getattr(self.hours, "non_hours")
        ret["caution_hours"] = getattr(self.hours, "dynamic_caution_hours")
        ret["state"] = getattr(self.chargecontroller, "state_display_model") #todo: fix this
        ret["currency"] = getattr(self.nordpool, "currency")
        ret["offsets"] = getattr(self.hours, "offsets", {})
        ret["average_nordpool_data"] = getattr(self.nordpool, "average_data")
        ret["use_cent"] = getattr(self.nordpool.model, "use_cent")
        ret["current_peak"] = getattr(self.sensors.current_peak, "value")
        ret["avg_kwh_price"] = await self.state_machine.async_add_executor_job(self.hours.get_average_kwh_price)
        ret["max_charge"] = await self.state_machine.async_add_executor_job(self.hours.get_total_charge)
        ret["average_weekly"] = getattr(self.nordpool, "average_weekly")
        ret["average_monthly"] = getattr(self.nordpool, "average_month")
        return ret

    @property
    def prices(self) -> list:
        if self.options.price.price_aware:
            return self.hours.prices
        return []

    @property
    def prices_tomorrow(self) -> list:
        if self.options.price.price_aware:
            return self.hours.prices_tomorrow
        return []

    @property
    def is_free_charge(self) -> bool:
        if hasattr(self.sensors, "locale"):
            return self.sensors.locale.data.free_charge(self.sensors.locale.data)
        return False

    @property
    def charger_done(self) -> bool:
        if hasattr(self.sensors, "charger_done"):
            return self.sensors.charger_done.value
        return False

    def _update_prices(self, prices: list) -> None:
        self.hours.update_prices(prices[0], prices[1])

    def _update_average_monthly_price(self, val) -> None:
        if self.options.price.price_aware and isinstance(val, float):
            self.hours.update_top_price(val)

    def _update_average_weekly_price(self, val) -> None:
        if self.options.price.price_aware and isinstance(val, float):
            setattr(self.hours, "adjusted_average", val)

    async def async_update_charger_done(self, val):
        setattr(self.sensors.charger_done, "value", bool(val))

    async def async_update_charger_enabled(self, val):
        await self.observer.async_broadcast("update latest charger start")
        if hasattr(self.sensors, "charger_enabled"):
            setattr(self.sensors.charger_enabled, "value", bool(val))
        else:
            raise Exception("Peaqev cannot function without a charger_enabled entity")


