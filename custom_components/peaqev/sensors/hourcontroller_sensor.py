from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.peaqev.peaqservice.hub.const import (
    AVERAGE_KWH_PRICE, AVERAGE_MONTHLY, AVERAGE_SPOTPRICE_DATA, CURRENCY,
    CURRENT_PEAK, FUTURE_HOURS, MAX_CHARGE, MAX_PRICE, MIN_PRICE,
    SPOTPRICE_SOURCE, USE_CENT)
from custom_components.peaqev.peaqservice.util.constants import HOURCONTROLLER
from custom_components.peaqev.sensors.money_sensor_helpers import *
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)

class HourControllerSensor(SensorBase, RestoreEntity):
    """Special sensor which is only created if priceaware is true"""
    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f'{hub.hubname} {HOURCONTROLLER}'
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._all_hours = None
        self._current_hour = None
        self._currency = None
        self._current_peak = None
        self._state = None
        self._avg_cost = None
        self._max_charge = None
        self._max_min_price = None
        self._source: str = ''
        self._average_spotprice_weekly = None
        self._max_price_based_on = None
        self._average_data_current_month = None
        self._secondary_threshold = None
        self._charge_permittance = None
        self._average_spotprice_data = {}

    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return 'mdi:car-clock'

    async def async_update(self) -> None:
        ret = await self.hub.async_request_sensor_data(
            CURRENCY,
            AVERAGE_SPOTPRICE_DATA,
            USE_CENT,
            CURRENT_PEAK,
            AVERAGE_KWH_PRICE,
            MAX_CHARGE,
            MAX_PRICE,
            MIN_PRICE,
            FUTURE_HOURS,
            AVERAGE_MONTHLY,
            SPOTPRICE_SOURCE
        )
        if ret is not None:
            self._state = await self.async_state_display()
            self._source = str(ret.get(SPOTPRICE_SOURCE)).capitalize()
            self._secondary_threshold = self.hub.spotprice.model.adjusted_average
            self._all_hours = set_all_hours_display(ret.get(FUTURE_HOURS, []), self.hub.spotprice.tomorrow_valid)
            self._currency = ret.get(CURRENCY)
            self._current_peak = ret.get(CURRENT_PEAK)
            self._max_charge = set_total_charge(ret.get(MAX_CHARGE))
            self._charge_permittance = set_current_charge_permittance_display(ret.get(FUTURE_HOURS))
            self._avg_cost = set_avg_cost(
                avg_cost=ret.get(AVERAGE_KWH_PRICE),
                currency=ret.get(CURRENCY),
                use_cent=ret.get(USE_CENT),
            )
            self._average_data_current_month = currency_translation(
                value=ret.get(AVERAGE_MONTHLY),
                currency=ret.get(CURRENCY),
                use_cent=ret.get(USE_CENT, False),
            )

            if self.hub.options.price.dynamic_top_price:
                _maxp = currency_translation(
                    value=ret.get(MAX_PRICE) if ret.get(MAX_PRICE, 0) > 0 else None,
                    currency=ret.get(CURRENCY),
                    use_cent=ret.get(USE_CENT, False),
                )
                _minp = currency_translation(
                    value=ret.get(MIN_PRICE) if ret.get(MIN_PRICE, 0) > 0 else None,
                    currency=ret.get(CURRENCY),
                    use_cent=ret.get(USE_CENT, False),
                )
                self._max_min_price = f'max:{_maxp}, min:{_minp}'
                self._max_price_based_on = (
                    self.hub.spotprice.model.dynamic_top_price_type
                )
                # todo: composition

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {
            'Current hour charge permittance': self._charge_permittance,
            'Avg price per kWh': self._avg_cost,
            'Max charge amount': self._max_charge,
            'All hours': self._all_hours,
            'Spotprice source': self._source
        }
        if self.hub.options.price.dynamic_top_price:
            attr_dict['Max price based on'] = self._max_price_based_on
            attr_dict['Max min price'] = self._max_min_price
        attr_dict['secondary_threshold'] = self._secondary_threshold
        return attr_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        _LOGGER.debug('last state of %s = %s', self._attr_name, state)
        if state:
            self._average_spotprice_weekly = (
                f'{self.hub.spotprice.average_weekly} {self._currency}'
            )
            self._average_data_current_month = (
                f'{self.hub.spotprice.average_month} {self._currency}'
            )
        else:
            self._average_spotprice_weekly = f'- {self._currency}'

    async def async_state_display(self) -> str:
        if self.hub.chargecontroller.is_initialized:
            if getattr(self.hub.hours.timer, 'is_override', False):  # todo: composition
                return getattr(
                    self.hub.hours.timer, 'override_string', ''
                )  # todo: composition
            return self.hub.hours.stopped_string  # todo: composition
        return getattr(
                    self.hub.chargecontroller, 'status_string', ''
                )  # todo: composition
