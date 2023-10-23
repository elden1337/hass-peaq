from __future__ import annotations

import logging
from datetime import datetime
from functools import partial
from typing import Callable

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change
from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.services.hourselection.initializers.hoursbase import Hours
from peaqevcore.services.prediction.prediction import Prediction
from peaqevcore.services.threshold.thresholdbase import ThresholdBase

from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import \
    IChargeController
from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.hub.const import *
from custom_components.peaqev.peaqservice.hub.hub_events import HubEvents
from custom_components.peaqev.peaqservice.hub.mixins.hub_getters_mixin import \
    HubGettersMixin
from custom_components.peaqev.peaqservice.hub.mixins.hub_initializer import \
    HubInitializerMixin
from custom_components.peaqev.peaqservice.hub.mixins.hub_setters_mixin import \
    HubSettersMixin
from custom_components.peaqev.peaqservice.hub.models.hub_model import HubModel
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.hub.observer.observer_coordinator import \
    Observer
from custom_components.peaqev.peaqservice.hub.sensors.ihub_sensors import \
    HubSensorsBase
from custom_components.peaqev.peaqservice.hub.servicecalls import ServiceCalls
from custom_components.peaqev.peaqservice.hub.spotprice.spotpricebase import \
    SpotPriceBase
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import \
    StateChangesBase
from custom_components.peaqev.peaqservice.powertools.ipower_tools import \
    IPowerTools
from custom_components.peaqev.peaqservice.util.extensionmethods import (
    async_iscoroutine, log_once)

_LOGGER = logging.getLogger(__name__)


class HomeAssistantHub(HubInitializerMixin, HubSettersMixin, HubGettersMixin):
    hub_id = 1337
    chargertype: IChargerType
    sensors: HubSensorsBase
    hours: Hours
    threshold: ThresholdBase
    prediction: Prediction
    servicecalls: ServiceCalls
    states: StateChangesBase
    chargecontroller: IChargeController
    spotprice: SpotPriceBase
    events :HubEvents
    power: IPowerTools #is interface only

    def __init__(self, hass: HomeAssistant, options: HubOptions, domain: str):
        self.model = HubModel(domain, hass)
        self.hubname = domain.capitalize()
        self.state_machine = hass
        self.options: HubOptions = options
        self._is_initialized = False
        self.observer = Observer(self)
        self._set_observers()

    async def async_setup(self):
        trackers = await self.async_setup_tracking()
        async_track_state_change(self.state_machine, trackers, self.async_state_changed)

    @property
    def enabled(self) -> bool:
        return self.sensors.charger_enabled.value

    @property
    def non_hours(self) -> list:
        return self.hours.non_hours

    @property
    def dynamic_caution_hours(self) -> dict:
        return self.hours.dynamic_caution_hours

    @property
    def is_initialized(self) -> bool:
        if self._is_initialized:
            return True
        if self.check_initializer():
            _LOGGER.debug("init hub is done")
            self.observer.activate(ObserverTypes.HubInitialized)
            self._is_initialized = True
            return True
        return False

    @property
    def watt_cost(self) -> int:
        return 0

    async def async_update_adjusted_average(self, val) -> None:
        pass

    async def async_update_average_monthly_price(self, val) -> None:
        pass

    async def async_update_spotprice(self) -> None:
        pass

    async def async_update_prices(self, prices: list) -> None:
        pass

    async def async_is_caution_hour(self) -> bool:
        return str(datetime.now().hour) in [str(h) for h in self.hours.caution_hours]

    @property
    def current_peak_dynamic(self):
        return self.sensors.current_peak.value

    @property
    def charger_done(self) -> bool:
        if hasattr(self.sensors, "charger_done"):
            return self.sensors.charger_done.value
        return False

    @property
    def purchased_average_month(self) -> float:
        try:
            month_draw = self.state_machine.states.get("sensor.peaqev_energy_including_car_monthly")
            month_cost = self.state_machine.states.get("sensor.peaqev_energy_cost_integral_monthly")
            if month_cost and month_draw:
                try:
                    return round(float(month_cost.state) / float(month_draw.state),3)
                except ValueError as v:
                    log_once(f"Unable to calculate purchased_average_month. {v}")
            return 0
        except ZeroDivisionError:
            return 0

    @property
    def savings_month(self) -> float:
        """Ackumulated savings for the month against spotprice avg. ie can fluctuate"""
        try:
            month_draw = self.state_machine.states.get("sensor.peaqev_energy_including_car_monthly")
            month_diff = self.spotprice.average_month - self.purchased_average_month
            if month_draw:
                return round(float(month_draw.state) * month_diff,3)
            return 0
        except ZeroDivisionError:
            return 0

    @callback
    async def async_state_changed(self, entity_id, old_state, new_state):
        if entity_id is not None:
            try:
                if old_state is None or old_state != new_state:
                    await self.states.async_update_sensor(entity_id, new_state.state)
            except Exception as e:
                msg = f"Unable to handle data-update: {entity_id} {old_state}|{new_state}. Exception: {e}"
                _LOGGER.error(msg)

    async def async_request_sensor_data(self, *args) -> dict | any:
        ret = {}
        if not self.is_initialized:
            return ret
        for arg in args:
            func: Callable = self._request_sensor_lookup().get(arg, None)
            if await async_iscoroutine(func):
                ret[arg] = await func()
            else:
                ret[arg] = func()
        self._check_max_min_total_charge(ret)
        if len(ret) == 1:
            """If only one value is requested, return the value instead of a dict"""
            val = list(ret.values())[0]
            if isinstance(val, str):
                return val.lower()
            return val
        return ret

    def _check_max_min_total_charge(self, ret: dict) -> None:
        pass

    def _request_sensor_lookup(self) -> dict:
        return {
            CHARGER_DONE: partial(getattr, self.sensors.charger_done, "value"),
            CHARGEROBJECT_VALUE:    partial(
                getattr, self.sensors.chargerobject, "value"
            ),
            HOUR_STATE:             partial(getattr, self.hours, "state", "unknown"),
            PRICES:                 partial(getattr, self.hours, "prices", []),
            PRICES_TOMORROW:        partial(getattr, self.hours, "prices_tomorrow", []),
            NON_HOURS:              partial(getattr, self, "non_hours", []),
            FUTURE_HOURS:           partial(getattr, self.hours, "future_hours", []),
            CAUTION_HOURS:          partial(getattr, self.hours, "caution_hours", []),
            DYNAMIC_CAUTION_HOURS:  partial(
                getattr, self, "dynamic_caution_hours", {}
            ),
            SPOTPRICE_SOURCE:       partial(getattr, self.spotprice, "source", "unknown"),
            AVERAGE_SPOTPRICE_DATA: partial(getattr, self.spotprice, "average_data"),
            USE_CENT:               partial(getattr, self.spotprice.model, "use_cent"),
            CURRENT_PEAK:           partial(getattr, self.sensors.current_peak, "value"),
            AVERAGE_KWH_PRICE:      partial(self.hours.async_get_average_kwh_price),
            MAX_CHARGE:             partial(self.hours.async_get_total_charge),
            AVERAGE_WEEKLY:         partial(getattr, self.spotprice, "average_weekly"),
            AVERAGE_MONTHLY:        partial(getattr, self.spotprice, "average_month"),
            AVERAGE_30:             partial(getattr, self.spotprice, "average_30"),
            CURRENCY:               partial(getattr, self.spotprice, "currency"),
            OFFSETS:                partial(getattr, self.hours, "offsets", {}),
            IS_PRICE_AWARE:         partial(getattr, self.options.price, "price_aware"),
            IS_SCHEDULER_ACTIVE: partial(
                getattr, self.hours.scheduler, "scheduler_active", False
            ),
            CHARGECONTROLLER_STATUS: partial(
                getattr, self.chargecontroller, "status_string"
            ),
            MAX_PRICE: partial(getattr, self.hours, "absolute_top_price"),
            MIN_PRICE: partial(getattr, self.hours, "min_price"),
            SAVINGS_PEAK: partial(
                getattr, self.chargecontroller.savings, "savings_peak"
            ),
            SAVINGS_TRADE: partial(
                getattr, self.chargecontroller.savings, "savings_trade"
            ),
            SAVINGS_TOTAL: partial(
                getattr, self.chargecontroller.savings, "savings_total"
            ),
            EXPORT_SAVINGS_DATA: partial(
                self.chargecontroller.savings.async_export_data
            ),
        }