from __future__ import annotations

import logging
import time
import traceback
from datetime import datetime
from functools import partial
from typing import Callable

# Third party imports
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change
# Local application imports
from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.common.spotprice.spotpricebase import SpotPriceBase
from peaqevcore.services.hourselection.initializers.hoursbase import Hours
from peaqevcore.services.prediction.prediction import Prediction
from peaqevcore.services.threshold.thresholdbase import ThresholdBase

from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import IChargeController
from custom_components.peaqev.peaqservice.chargertypes.icharger_type import IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.hub.const import LookupKeys
from custom_components.peaqev.peaqservice.hub.factories.hourselection_factory import HourselectionFactory
from custom_components.peaqev.peaqservice.hub.hub_events import HubEvents
from custom_components.peaqev.peaqservice.hub.models.hub_model import HubModel
from custom_components.peaqev.peaqservice.hub.models.hub_options import HubOptions
from custom_components.peaqev.peaqservice.hub.models.initializer_types import InitializerTypes
from custom_components.peaqev.peaqservice.hub.observer.observer_coordinator import Observer
from custom_components.peaqev.peaqservice.hub.sensors.hub_sensors_base import HubSensorsBase
from custom_components.peaqev.peaqservice.hub.servicecalls import ServiceCalls
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import StateChangesBase
from custom_components.peaqev.peaqservice.powertools.ipower_tools import IPowerTools
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER
from custom_components.peaqev.peaqservice.util.extensionmethods import async_iscoroutine, log_once, nametoid
from custom_components.peaqev.peaqservice.util.schedule_options_handler import SchedulerOptionsHandler

_LOGGER = logging.getLogger(__name__)

class HubInitializer:
    initialized_log_last_logged = 0
    not_ready_list_old_state = 0
    _initialized: bool = False

class HomeAssistantHub:
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
    initialized_log_last_logged = 0
    not_ready_list_old_state = 0
    _initialized: bool = False

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
    def is_initialized(self) -> bool:
        if self._is_initialized:
            return True
        if self.check_initializer():
            _LOGGER.debug('init hub is done')
            self.observer.activate(ObserverTypes.HubInitialized)
            self._is_initialized = True
            return True
        return False

    @property
    def watt_cost(self) -> int:
        return 0

    @property
    def scheduler_options_handler(self) -> SchedulerOptionsHandler|None:
        return None

    @property
    def current_peak_dynamic(self):
        return self.sensors.current_peak.observed_peak

    @property
    def charger_done(self) -> bool:
        if hasattr(self.sensors, 'charger_done'):
            return self.sensors.charger_done.value
        return False

    @property
    def purchased_average_month(self) -> float:
        try:
            month_draw = self.state_machine.states.get('sensor.peaqev_energy_including_car_monthly')
            month_cost = self.state_machine.states.get('sensor.peaqev_energy_cost_integral_monthly')
            if month_cost and month_draw:
                try:
                    return round(float(month_cost.state) / float(month_draw.state),3)
                except ValueError as v:
                    log_once(f'Unable to calculate purchased_average_month. {v}', 'warning')
            return 0
        except ZeroDivisionError:
            return 0

    @property
    def savings_month(self) -> float:
        """Accumulated savings for the month against spotprice avg. ie can fluctuate"""
        try:
            month_draw = self.state_machine.states.get('sensor.peaqev_energy_including_car_monthly')
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
                tb = traceback.format_exc()  # Get the full traceback
                msg = f'Unable to handle data-update: {entity_id} {old_state}|{new_state}. Exception: {e}\n{tb}'
                _LOGGER.error(msg)

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
            val = list(ret.values())[0]
            if isinstance(val, str):
                return val.lower()
            return val
        return ret

    def _check_max_min_total_charge(self, ret: dict) -> None:
        pass

    def _request_sensor_lookup(self) -> dict:
        """Proxies the request to the correct sensor."""
        return {
            LookupKeys.CHARGER_DONE: partial(getattr, self.sensors.charger_done, 'value'),
            LookupKeys.CHARGEROBJECT_VALUE:    partial(
                getattr, self.sensors.chargerobject, 'value'
            ),
            LookupKeys.HOUR_STATE:             partial(getattr, self.hours, 'state', 'unknown'),
            LookupKeys.PRICES:                 partial(getattr, self.hours, 'prices', []),
            LookupKeys.PRICES_TOMORROW:        partial(getattr, self.hours, 'prices_tomorrow', []),
            LookupKeys.NON_HOURS:              partial(getattr, self.hours, 'non_hours', []),
            LookupKeys.FUTURE_HOURS:           partial(getattr, self.hours, 'future_hours', []),
            LookupKeys.CAUTION_HOURS:          partial(getattr, self.hours, 'caution_hours', []),
            LookupKeys.DYNAMIC_CAUTION_HOURS:  partial(
                getattr, self.hours, 'dynamic_caution_hours', {}
            ),
            LookupKeys.SPOTPRICE_SOURCE:       partial(getattr, self.spotprice, 'source', 'unknown'),
            LookupKeys.AVERAGE_SPOTPRICE_DATA: partial(getattr, self.spotprice, 'average_data'),
            LookupKeys.AVERAGE_STDEV_DATA:     partial(getattr, self.spotprice, 'average_stdev_data'),
            LookupKeys.USE_CENT:               partial(getattr, self.spotprice.model, 'use_cent'),
            LookupKeys.CURRENT_PEAK:           partial(getattr, self.sensors.current_peak, 'observed_peak'),
            LookupKeys.AVERAGE_KWH_PRICE:      partial(self.hours.async_get_average_kwh_price),
            LookupKeys.MAX_CHARGE:             partial(self.hours.async_get_total_charge),
            LookupKeys.AVERAGE_WEEKLY:         partial(getattr, self.spotprice, 'average_weekly'),
            LookupKeys.AVERAGE_MONTHLY:        partial(getattr, self.spotprice, 'average_month'),
            LookupKeys.AVERAGE_30:             partial(getattr, self.spotprice, 'average_30'),
            LookupKeys.CURRENCY:               partial(getattr, self.spotprice, 'currency'),
            LookupKeys.OFFSETS:                partial(getattr, self.hours, 'offsets', {}),
            LookupKeys.IS_PRICE_AWARE:         partial(getattr, self.options.price, 'price_aware'),
            LookupKeys.IS_SCHEDULER_ACTIVE: partial(
                getattr, self.hours.scheduler, 'scheduler_active', False
            ),
            LookupKeys.SCHEDULES: partial(
                getattr, self.hours.scheduler, 'schedules', {}
            ),
            LookupKeys.CHARGECONTROLLER_STATUS: partial(
                getattr, self.chargecontroller, 'status_string'
            ),
            LookupKeys.MAX_PRICE: partial(getattr, self.hours, 'absolute_top_price'),
            LookupKeys.MIN_PRICE: partial(getattr, self.hours, 'min_price'),
            LookupKeys.SAVINGS_PEAK: partial(
                getattr, self.chargecontroller.savings, 'savings_peak'
            ),
            LookupKeys.SAVINGS_TRADE: partial(
                getattr, self.chargecontroller.savings, 'savings_trade'
            ),
            LookupKeys.SAVINGS_TOTAL: partial(
                getattr, self.chargecontroller.savings, 'savings_total'
            ),
            LookupKeys.EXPORT_SAVINGS_DATA: partial(
                self.chargecontroller.savings.async_export_data
            ),
        }

    def now_is_non_hour(self) -> bool:
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        non_hours = self._request_sensor_lookup().get(LookupKeys.NON_HOURS, [])
        return now in non_hours

    def now_is_caution_hour(self) -> bool:
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        caution_hours = self._request_sensor_lookup().get(LookupKeys.DYNAMIC_CAUTION_HOURS, {})
        return now in caution_hours.keys()

    async def async_free_charge(self) -> bool:
        """Returns true if free charge is enabled, which means that peaks are currently not tracked"""
        try:
            return await self.sensors.locale.data.async_free_charge()
        except Exception as e:
            _LOGGER.debug(f'Unable to get free charge. Exception: {e}')
            return False

    async def async_predictedpercentageofpeak(self):
        ret = await self.prediction.async_predicted_percentage_of_peak(
            predicted_energy=await self.async_get_predicted_energy(),
            peak=self.sensors.current_peak.observed_peak,
        )
        self.model.peak_breached = ret > 100
        return ret

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

    async def async_get_predicted_energy(self) -> float:
        ret = await self.prediction.async_predicted_energy(
            power_avg=self.sensors.powersensormovingaverage.value,
            total_hourly_energy=self.sensors.totalhourlyenergy.value,
            is_quarterly=await self.sensors.locale.data.async_is_quarterly(),
        )
        return ret

    def check_initializer(self):
        if self._initialized:
            return True
        else:
            return self._check

    def _check(self) -> bool:
        init_types = {InitializerTypes.Hours: self.hours.is_initialized}
        if self.options.price.price_aware:
            init_types[InitializerTypes.SpotPrice] = self.spotprice.is_initialized
        if hasattr(self.sensors, 'carpowersensor'):
            init_types[InitializerTypes.CarPowerSensor] = self.sensors.carpowersensor.is_initialized
        if hasattr(self.sensors, 'chargerobject_switch'):
            init_types[
                InitializerTypes.ChargerObjectSwitch
            ] = self.sensors.chargerobject_switch.is_initialized
        if hasattr(self.sensors, 'power'):
            init_types[InitializerTypes.Power] = self.sensors.power.is_initialized
        if hasattr(self.sensors, 'chargerobject'):
            init_types[InitializerTypes.ChargerObject] = self.sensors.chargerobject.is_initialized
        init_types[InitializerTypes.ChargerType] = self.chargertype.is_initialized
        if all(init_types.values()):
            self._initialized = True
            _LOGGER.info('Hub is ready to use.')
            _LOGGER.debug(
                f'Hub is initialized with {self.options.price.cautionhour_type} as cautionhourtype.'
            )
            return True
        return self.scramble_not_initialized(init_types)

    def scramble_not_initialized(self, init_types) -> bool:
        not_ready = [r.value for r in init_types if init_types[r] is False]
        if any(
                [
                    len(not_ready) != self.not_ready_list_old_state,
                    self.initialized_log_last_logged - time.time() > 30,
                ]
        ):
            _LOGGER.debug(f'Hub is awaiting {not_ready} before being ready to use.')
            self.not_ready_list_old_state = len(not_ready)
            self.initialized_log_last_logged = time.time()
        if [InitializerTypes.ChargerObject, InitializerTypes.ChargerType] in not_ready:
            if self.chargertype.async_setup():
                self.chargertype.is_initialized = True
        return False

    async def async_init_hours(self):
        self.hours = await HourselectionFactory.async_create(self)
        if self.options.price.price_aware:
            await self.hours.async_update_prices(
                self.spotprice.model.prices,
                self.spotprice.model.prices_tomorrow)
        _LOGGER.debug('Re-initializing Hoursclasses.')

    async def async_setup_tracking(self) -> list:
        tracker_entities = []
        if not self.options.peaqev_lite:
            tracker_entities.append(self.options.powersensor)
            tracker_entities.append(self.sensors.totalhourlyenergy.entity)
        self.model.chargingtracker_entities = await self.async_set_chargingtracker_entities()
        tracker_entities += self.model.chargingtracker_entities
        return tracker_entities

    async def async_set_chargingtracker_entities(self) -> list:
        ret = [f'sensor.{self.model.domain}_{nametoid(CHARGERCONTROLLER)}']
        if hasattr(self.sensors, 'chargerobject_switch'):
            ret.append(self.sensors.chargerobject_switch.entity)
        if hasattr(self.sensors, 'carpowersensor'):
            ret.append(self.sensors.carpowersensor.entity)
        if hasattr(self.sensors, 'charger_enabled'):
            ret.append(self.sensors.charger_enabled.entity)
        if hasattr(self.sensors, 'charger_done'):
            ret.append(self.sensors.charger_done.entity)
        if self.chargertype.type not in [ChargerType.Outlet, ChargerType.NoCharger]:
            ret.append(self.sensors.chargerobject.entity)
        if not self.options.peaqev_lite:
            ret.append(self.sensors.powersensormovingaverage.entity)
            ret.append(self.sensors.powersensormovingaverage24.entity)
        if self.options.price.price_aware:
            ret.append(getattr(self.spotprice, 'entity', ''))
        return ret

    def _set_observers(self) -> None:
        self.observer.add(ObserverTypes.PricesChanged, self.async_update_prices)
        self.observer.add(
            ObserverTypes.AdjustedAveragePriceChanged, self.async_update_adjusted_average
        )
        self.observer.add(ObserverTypes.UpdateChargerDone, self.async_update_charger_done)
        self.observer.add(ObserverTypes.UpdateChargerEnabled, self.async_update_charger_enabled)
        self.observer.add(
            ObserverTypes.DynamicMaxPriceChanged, self.async_update_average_monthly_price
        )
        self.observer.add(ObserverTypes.UpdatePeak, self.async_update_peak)

    async def async_set_init_dict(self, init_dict, override: bool = False) -> None:
        await self.sensors.locale.data.query_model.peaks.async_set_init_dict(init_dict, override=override)
        try:
            ff = getattr(self.sensors.locale.data.query_model.peaks, 'export_peaks', {})
            _LOGGER.debug(f'intialized_peaks: {ff}')
        except Exception as e:
            _LOGGER.Exception(f'Unable to set init_dict: {e}')

    async def async_set_chargerobject_value(self, value) -> None:
        if hasattr(self.sensors, 'chargerobject'):
            setattr(self.sensors.chargerobject, 'value', value)

    async def async_update_peak(self, val) -> None:
        await self.sensors.locale.async_try_update_peak(
            new_val=val[0], timestamp=val[1]
        )
        checkval = self.sensors.current_peak.observed_peak
        self.sensors.current_peak.observed_peak = (
            list(self.sensors.locale.data.query_model.peaks.p.values())
        )
        if checkval != self.sensors.current_peak.observed_peak:
            _LOGGER.info('observed peak updated to %s', self.sensors.current_peak.observed_peak)

    async def async_update_charger_done(self, val):
        setattr(self.sensors.charger_done, 'value', bool(val))

    async def async_update_charger_enabled(self, val):
        await self.observer.async_broadcast(ObserverTypes.UpdateLatestChargerStart)
        if hasattr(self.sensors, 'charger_enabled'):
            setattr(self.sensors.charger_enabled, 'value', bool(val))
        else:
            raise Exception('Peaqev cannot function without a charger_enabled entity')
