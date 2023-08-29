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
from custom_components.peaqev.peaqservice.chargertypes.chargertype_factory import \
    ChargerTypeFactory
from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.const import *
from custom_components.peaqev.peaqservice.hub.factories.hourselection_factory import \
    HourselectionFactory
from custom_components.peaqev.peaqservice.hub.factories.threshold_factory import \
    ThresholdFactory
from custom_components.peaqev.peaqservice.hub.hub_events import HubEvents
from custom_components.peaqev.peaqservice.hub.hub_initializer import \
    HubInitializer
from custom_components.peaqev.peaqservice.hub.max_min_controller import \
    MaxMinController
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.hub.observer.observer_coordinator import \
    Observer
from custom_components.peaqev.peaqservice.hub.sensors.hubsensors_factory import \
    HubSensorsFactory
from custom_components.peaqev.peaqservice.hub.sensors.ihub_sensors import \
    HubSensors
from custom_components.peaqev.peaqservice.hub.servicecalls import ServiceCalls
from custom_components.peaqev.peaqservice.hub.spotprice.ispotprice import ISpotPrice
from custom_components.peaqev.peaqservice.hub.spotprice.spotprice_factory import SpotPriceFactory
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import \
    IStateChanges
from custom_components.peaqev.peaqservice.hub.state_changes.state_changes_factory import \
    StateChangesFactory
from custom_components.peaqev.peaqservice.powertools.powertools_factory import \
    PowerToolsFactory
from custom_components.peaqev.peaqservice.util.constants import \
    CHARGERCONTROLLER
from custom_components.peaqev.peaqservice.util.extensionmethods import (
    async_iscoroutine, nametoid)

_LOGGER = logging.getLogger(__name__)


class HomeAssistantHub:
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
        self.initializer = HubInitializer(self)
        self.max_min_controller = MaxMinController(self)

    async def setup(self):
        self.chargertype = await ChargerTypeFactory.async_create(
            self.state_machine, self.options
        )  # chargecontroller
        self.sensors: HubSensors = await HubSensorsFactory.async_create(hub=self)
        self.chargecontroller = await ChargeControllerFactory.async_create(
            self,
            charger_states=self.chargertype.chargerstates,
            charger_type=self.chargertype.type,
        )
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
            if datetime.now().hour in self.dynamic_caution_hours.keys() and not getattr(
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
            if self.initializer.check():
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

    @callback
    async def async_state_changed(self, entity_id, old_state, new_state):
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
        ret = [f"sensor.{self.domain}_{nametoid(CHARGERCONTROLLER)}"]
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
        if self.options.price.price_aware:
            ret.append(getattr(self.spotprice, "entity", ""))
        return ret

    def _set_observers(self) -> None:
        self.observer.add("prices changed", self.async_update_prices)
        self.observer.add(
            "adjusted average price changed", self.async_update_adjusted_average
        )
        self.observer.add("update charger done", self.async_update_charger_done)
        self.observer.add("update charger enabled", self.async_update_charger_enabled)
        self.observer.add(
            "dynamic max price changed", self.async_update_average_monthly_price
        )

    """Composition below here"""

    async def async_set_init_dict(self, init_dict):
        await self.sensors.locale.data.query_model.peaks.async_set_init_dict(
            init_dict
        )
        try:
            ff = getattr(self.sensors.locale.data.query_model.peaks, "export_peaks", {})
            _LOGGER.debug(f"intialized_peaks: {ff}")
        except Exception:
            pass

    def get_power_sensor_from_hass(self) -> float | None:
        ret = self.state_machine.states.get(self.options.powersensor)
        if ret is not None:
            try:
                return float(ret.state)
            except Exception:
                return None
        return ret

    async def async_set_chargerobject_value(self, value) -> None:
        if hasattr(self.sensors, "chargerobject"):
            setattr(self.sensors.chargerobject, "value", value)

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

    def now_is_non_hour(self) -> bool:
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        return now in self.non_hours

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

    async def async_free_charge(self) -> bool:
        try:
            return await self.sensors.locale.data.async_free_charge()
        except Exception:
            return False

    @property
    def charger_done(self) -> bool:
        if hasattr(self.sensors, "charger_done"):
            return self.sensors.charger_done.value
        return False

    async def async_update_prices(self, prices: list) -> None:
        if self.options.price.price_aware:
            await self.hours.async_update_prices(prices[0], prices[1])
            if self.max_min_controller.is_on:
                await self.hours.async_update_max_min(
                    max_charge=self.max_min_controller.max_charge,
                    car_connected=self.chargecontroller.connected,
                    session_energy=self.chargecontroller.session.session_energy,
                )

    async def async_update_average_monthly_price(self, val) -> None:
        if self.options.price.price_aware and isinstance(val, float):
            await self.hours.async_update_top_price(val)

    async def async_update_adjusted_average(self, val) -> None:
        if self.options.price.price_aware and isinstance(val, float):
            await self.hours.async_update_adjusted_average(val)

    async def async_update_charger_done(self, val):
        setattr(self.sensors.charger_done, "value", bool(val))

    async def async_update_charger_enabled(self, val):
        await self.observer.async_broadcast("update latest charger start")
        if hasattr(self.sensors, "charger_enabled"):
            setattr(self.sensors.charger_enabled, "value", bool(val))
        else:
            raise Exception("Peaqev cannot function without a charger_enabled entity")

    async def async_predictedpercentageofpeak(self):
        return await self.prediction.async_predicted_percentage_of_peak(
            predicted_energy=await self.async_get_predicted_energy(),
            peak=self.sensors.current_peak.value,
        )

    async def async_threshold_start(self):
        return await self.threshold.async_start(
            is_caution_hour=await self.async_is_caution_hour(),
            is_quarterly=await self.sensors.locale.data.async_is_quarterly(),
        )

    async def async_threshold_stop(self):
        return await self.threshold.async_stop(
            is_caution_hour=await self.async_is_caution_hour(),
            is_quarterly=await self.sensors.locale.data.async_is_quarterly(),
        )

    async def async_is_caution_hour(self) -> bool:
        if self.options.price.price_aware:
            return False
        return str(datetime.now().hour) in self.hours.caution_hours

    async def async_get_predicted_energy(self) -> float:
        ret = await self.prediction.async_predicted_energy(
            power_avg=self.sensors.powersensormovingaverage.value,
            total_hourly_energy=self.sensors.totalhourlyenergy.value,
            is_quarterly=await self.sensors.locale.data.async_is_quarterly(),
        )
        return ret
