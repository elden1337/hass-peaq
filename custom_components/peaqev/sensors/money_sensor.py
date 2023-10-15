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
from custom_components.peaqev.sensors.sensorbase import MoneyDevice, SensorBase

_LOGGER = logging.getLogger(__name__)


class PeaqMoneyDataSensor(MoneyDevice, RestoreEntity):
    """Holding spotprice average data"""

    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f"{hub.hubname} {AVERAGE_SPOTPRICE_DATA}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None
        self._average_spotprice_data = {}

    @property
    def icon(self) -> str:
        return "mdi:database-outline"

    async def async_update(self) -> None:
        ret = await self.hub.async_request_sensor_data(
            AVERAGE_SPOTPRICE_DATA,
        )
        if ret is not None:
            if len(ret):
                self._state = "on"
                if ret != self._average_spotprice_data:
                    _diff = self.diff_dicts(self._average_spotprice_data, ret)
                    _LOGGER.debug(f"dict was changed: added: {_diff[0]}, removed: {_diff[1]}")
                self._average_spotprice_data = ret
                self.hub.spotprice.converted_average_data = True

    @staticmethod
    def diff_dicts(dict1, dict2):
        added = {}
        removed = {}

        for key in dict2:
            if key not in dict1:
                added[key] = dict2[key]

        for key in dict1:
            if key not in dict2:
                removed[key] = dict1[key]

        return added, removed

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {"Spotprice average data":   self._average_spotprice_data }
        return attr_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        _LOGGER.debug("last state of %s = %s", self._attr_name, state)
        if state:
            self._state = "on"
            data = state.attributes.get("Spotprice average data", [])
            if len(data):
                self.hub.spotprice.converted_average_data = True
                await self.hub.spotprice.async_import_average_data(data)
                self._average_spotprice_data = self.hub.spotprice.average_data

class PeaqMoneySensor(SensorBase, RestoreEntity):
    """Special sensor which is only created if priceaware is true"""
    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f"{hub.hubname} {HOURCONTROLLER}"
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
        self._source: str = ""
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
        return "mdi:car-clock"

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
            if not self.hub.spotprice.converted_average_data:
                self._average_spotprice_data = ret.get(AVERAGE_SPOTPRICE_DATA, [])
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
                self._max_min_price = f"max:{_maxp}, min:{_minp}"
                self._max_price_based_on = (
                    self.hub.spotprice.model.dynamic_top_price_type
                )
                # todo: composition

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {
            "Current hour charge permittance": self._charge_permittance,
            "Avg price per kWh": self._avg_cost,
            "Max charge amount": self._max_charge,
            "All hours": self._all_hours,
            "Spotprice source": self._source
        }
        if not self.hub.spotprice.converted_average_data:
            attr_dict["Spotprice average data"] = self._average_spotprice_data
        if self.hub.options.price.dynamic_top_price:
            attr_dict["Max price based on"] = self._max_price_based_on
            attr_dict["Max min price"] = self._max_min_price
        attr_dict["secondary_threshold"] = self._secondary_threshold
        return attr_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        _LOGGER.debug("last state of %s = %s", self._attr_name, state)
        if state:
            if not self.hub.spotprice.converted_average_data:
                #mockdata = {"2023-08-28":1.551,"2023-08-29":1.027,"2023-08-30":1.606,"2023-08-31":1.486,"2023-09-01":0.715,"2023-09-02":0.38,"2023-09-03":0.356,"2023-09-04":0.257,"2023-09-05":0.216,"2023-09-06":0.716,"2023-09-07":0.773,"2023-09-08":1.296,"2023-09-09":0.234,"2023-09-10":0.241,"2023-09-11":0.978,"2023-09-12":0.229,"2023-09-13":1.032,"2023-09-14":1.356,"2023-09-15":0.451,"2023-09-16":0.242,"2023-09-17":0.224,"2023-09-18":0.2,"2023-09-19":0.08,"2023-09-20":0.105,"2023-09-21":0.099,"2023-09-22":0.091,"2023-09-23":0.121,"2023-09-24":0.113,"2023-09-25":0.077,"2023-09-26":0.194,"2023-09-27":0.235}
                # await self.hub.spotprice.async_import_average_data(
                #     mockdata)
                data = state.attributes.get("Spotprice average data", state.attributes.get("Nordpool average data", []))
                if len(data):
                    await self.hub.spotprice.async_import_average_data(data)
                    self._average_spotprice_data = self.hub.spotprice.average_data
            self._average_spotprice_weekly = (
                f"{self.hub.spotprice.average_weekly} {self._currency}"
            )
            self._average_data_current_month = (
                f"{self.hub.spotprice.average_month} {self._currency}"
            )
        else:
            self._average_spotprice_weekly = f"- {self._currency}"

    async def async_state_display(self) -> str:
        if self.hub.chargecontroller.is_initialized:
            if getattr(self.hub.hours.timer, "is_override", False):  # todo: composition
                return getattr(
                    self.hub.hours.timer, "override_string", ""
                )  # todo: composition
            return self.hub.hours.stopped_string  # todo: composition
        return getattr(
                    self.hub.chargecontroller, "status_string", ""
                )  # todo: composition
