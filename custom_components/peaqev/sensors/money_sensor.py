from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

import logging
from datetime import datetime

from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.peaqev.peaqservice.chargecontroller.const import \
    CHARGING_ALLOWED
from custom_components.peaqev.peaqservice.util.constants import HOURCONTROLLER
from custom_components.peaqev.sensors.money_sensor_helpers import (
    async_currency_translation, async_set_avg_cost,
    async_set_caution_hours_display,
    async_set_current_charge_permittance_display, async_set_non_hours_display,
    async_set_total_charge, calculate_stop_len)
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)


class PeaqMoneySensor(SensorBase, RestoreEntity):
    """Special sensor which is only created if priceaware is true"""

    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f"{hub.hubname} {HOURCONTROLLER}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._nonhours = None
        self._dynamic_caution_hours = None
        self._current_hour = None
        self._currency = None
        self._current_peak = None
        self._state = None
        self._avg_cost = None
        self._max_charge = None
        self._average_nordpool = None
        self._average_data_current_month = None
        self._charge_permittance = None
        self._offsets = {}
        self._average_nordpool_data = []

    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:car-clock"

    async def async_update(self) -> None:
        ret = await self.hub.async_request_sensor_data(
            "prices_tomorrow",
            "non_hours",
            "dynamic_caution_hours",
            "currency",
            "offsets",
            "average_nordpool_data",
            "use_cent",
            "current_peak",
            "avg_kwh_price",
            "max_charge",
            "average_weekly",
            "average_monthly",
        )
        if ret is not None:
            self._state = await self.async_state_display(
                ret.get("non_hours"), ret.get("dynamic_caution_hours")
            )
            self._nonhours = await async_set_non_hours_display(
                ret.get("non_hours"), ret.get("prices_tomorrow")
            )
            self._dynamic_caution_hours = await async_set_caution_hours_display(
                ret.get("dynamic_caution_hours")
            )
            self._currency = ret.get("currency")
            self._offsets = ret.get("offsets", {})
            self._current_peak = ret.get("current_peak")
            self._max_charge = await async_set_total_charge(ret.get('max_charge'))
            self._average_nordpool_data = ret.get("average_nordpool_data", [])
            self._charge_permittance = await async_set_current_charge_permittance_display(
                ret.get("non_hours"), ret.get("dynamic_caution_hours")
            )

            self._avg_cost = await async_set_avg_cost(
                avg_cost=ret.get("avg_kwh_price"),
                currency=ret.get("currency"),
                use_cent=ret.get("use_cent"),
            )

            self._average_nordpool = await async_currency_translation(
                value=ret.get("average_weekly"),
                currency=ret.get("currency"),
                use_cent=ret.get("use_cent"),
            )
            self._average_data_current_month = await async_currency_translation(
                value=ret.get("average_monthly"),
                currency=ret.get("currency"),
                use_cent=ret.get("use_cent"),
            )

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {
            "Non hours": self._nonhours,
            "Caution hours": self._dynamic_caution_hours,
            "Current hour charge permittance": self._charge_permittance,
            "Avg price per kWh": self._avg_cost,
            "Max charge amount": self._max_charge,
            "Nordpool average 7 days": self._average_nordpool,
            "nordpool_average_this_month": self._average_data_current_month,
            "Nordpool average data": self._average_nordpool_data,
            "offsets": self._offsets,
        }
        return attr_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        _LOGGER.debug("last state of %s = %s", self._attr_name, state)
        if state:
            await self.hub.nordpool.async_import_average_data(
                state.attributes.get("Nordpool average data", 50)
            )
            self._average_nordpool_data = list(state.attributes.get("Nordpool average data", 50))
            self._average_nordpool = f"{self.hub.nordpool.average_weekly} {self._currency}"
            self._average_data_current_month = f"{self.hub.nordpool.average_month} {self._currency}"
        else:
            self._average_nordpool = f"- {self._currency}"

    async def async_state_display(self, non_hours: list, dynamic_caution_hours: dict) -> str:
        hour = datetime.now().hour
        ret = CHARGING_ALLOWED.capitalize()
        if getattr(self.hub.hours.timer, "is_override", False):  # todo: composition
            self._icon = "mdi:car-electric-outline"
            return getattr(self.hub.hours.timer, "override_string", "")  # todo: composition
        if hour in non_hours:
            self._icon = "mdi:car-clock"
            ret = calculate_stop_len(non_hours)
        elif hour in dynamic_caution_hours.keys():
            val = dynamic_caution_hours.get(hour)
            ret += f" at {int(val * 100)}% of peak"
        return ret
