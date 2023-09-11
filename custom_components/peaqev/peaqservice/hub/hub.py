from __future__ import annotations

import logging
from datetime import datetime
from functools import partial
from typing import Callable

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change
from peaqevcore.services.hourselection.initializers.hoursbase import Hours
from peaqevcore.services.prediction.prediction import Prediction
from peaqevcore.services.threshold.thresholdbase import ThresholdBase

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_factory import \
    ChargeControllerFactory
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import \
    IChargeController
from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.hub.const import *
from custom_components.peaqev.peaqservice.hub.factories.hourselection_factory import \
    HourselectionFactory
from custom_components.peaqev.peaqservice.hub.factories.threshold_factory import \
    ThresholdFactory
from custom_components.peaqev.peaqservice.hub.hub_events import HubEvents
from custom_components.peaqev.peaqservice.hub.max_min_controller import \
    MaxMinController
from custom_components.peaqev.peaqservice.hub.mixins.hub_getters_mixin import \
    HubGettersMixin
from custom_components.peaqev.peaqservice.hub.mixins.hub_initializer import \
    HubInitializerMixin
from custom_components.peaqev.peaqservice.hub.mixins.hub_setters_mixin import \
    HubSettersMixin
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.hub.observer.observer_coordinator import \
    Observer
from custom_components.peaqev.peaqservice.hub.sensors.hubsensors_factory import \
    HubSensorsFactory
from custom_components.peaqev.peaqservice.hub.sensors.ihub_sensors import \
    HubSensors
from custom_components.peaqev.peaqservice.hub.servicecalls import ServiceCalls
from custom_components.peaqev.peaqservice.hub.spotprice.ispotprice import \
    ISpotPrice
from custom_components.peaqev.peaqservice.hub.spotprice.spotprice_factory import \
    SpotPriceFactory
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import \
    IStateChanges
from custom_components.peaqev.peaqservice.hub.state_changes.state_changes_factory import \
    StateChangesFactory
from custom_components.peaqev.peaqservice.powertools.powertools_factory import \
    PowerToolsFactory
from custom_components.peaqev.peaqservice.util.extensionmethods import \
    async_iscoroutine

_LOGGER = logging.getLogger(__name__)


class HomeAssistantHub(HubInitializerMixin, HubSettersMixin, HubGettersMixin):
    hub_id = 1337
    chargertype: IChargerType
    sensors: HubSensors
    hours: Hours
    threshold: ThresholdBase
    prediction: Prediction
    servicecalls: ServiceCalls
    states: IStateChanges
    chargecontroller: IChargeController
    spotprice: ISpotPrice
    events :HubEvents

    def __init__(self, hass: HomeAssistant, options: HubOptions, domain: str):
        self.chargingtracker_entities = []
        self.power = None
        self.hubname = domain.capitalize()
        self.domain = domain
        self.state_machine = hass
        self.options: HubOptions = options
        self._is_initialized = False
        self.observer = Observer(self)
        self._set_observers()
        self.max_min_controller = MaxMinController(self)

    async def setup(self):
        self.sensors: HubSensors = await HubSensorsFactory.async_create(hub=self)
        self.chargecontroller = await ChargeControllerFactory.async_create(self)
        self.hours: Hours = await HourselectionFactory.async_create(self)  # top level
        self.threshold: ThresholdBase = await ThresholdFactory.async_create(
            self
        )  # top level
        self.prediction = Prediction(self)  # threshold
        self.servicecalls = ServiceCalls(self)  # top level
        self.states = await StateChangesFactory.async_create(self)  # top level
        self.spotprice: ISpotPrice = SpotPriceFactory.create(hub=self, test=False, is_active=self.options.price.price_aware)
        self.power = await PowerToolsFactory.async_create(self)
        self.events = HubEvents(self, self.state_machine)
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
    def current_peak_dynamic(self):
        """Dynamically calculated peak to adhere to caution-hours"""
        if self.options.price.price_aware and len(self.dynamic_caution_hours) > 0:
            if datetime.now().replace(minute=0,second=0,microsecond=0) in self.dynamic_caution_hours.keys() and not getattr(
                self.hours.timer, "is_override", False
            ):
                return (
                    self.sensors.current_peak.value
                    * self.dynamic_caution_hours[datetime.now().hour]
                )
        return self.sensors.current_peak.value

    @property
    def is_initialized(self) -> bool:
        if not self._is_initialized:
            if self.check_initializer():
                self.observer.activate("hub initialized")
                self._is_initialized = True
                return True
            return False
        return True

    @property
    def watt_cost(self) -> int:
        if self.options.price.price_aware:
            try:
                return int(
                    round(
                        float(self.sensors.power.total.value)
                        * float(self.spotprice.state),
                        0,
                    )
                )
            except Exception as e:
                _LOGGER.error(f"Unable to calculate watt cost. Exception: {e}")
                return 0
        return 0

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
    def charger_done(self) -> bool:
        if hasattr(self.sensors, "charger_done"):
            return self.sensors.charger_done.value
        return False

    @callback
    async def async_state_changed(self, entity_id, old_state, new_state):
        if entity_id is not None:
            try:
                if old_state is None or old_state != new_state:
                    await self.states.async_update_sensor(entity_id, new_state.state)
            except Exception as e:
                msg = f"Unable to handle data-update: {entity_id} {old_state}|{new_state}. Exception: {e}"
                _LOGGER.error(msg)

    def get_power_sensor_from_hass(self) -> float | None:
        ret = self.state_machine.states.get(self.options.powersensor)
        if ret is not None:
            try:
                return float(ret.state)
            except Exception:
                return None
        return ret

    async def async_request_sensor_data(self, *args) -> dict | any:
        if not self.is_initialized:
            return {}
        lookup = {
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
        ret = {}
        for arg in args:
            func: Callable = lookup.get(arg, None)
            if await async_iscoroutine(func):
                ret[arg] = await func()
            else:
                ret[arg] = func()
        if "max_charge" in ret.keys():
            self.max_min_controller._original_total_charge = ret["max_charge"][0]
            # todo: 247
        if len(ret) == 1:
            val = list(ret.values())[0]
            if isinstance(val, str):
                return val.lower()
            return val
        return ret


