import logging
from datetime import datetime

from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.peaqev.peaqservice.chargecontroller.const import CHARGING_ALLOWED
from custom_components.peaqev.peaqservice.util.constants import HOURCONTROLLER
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)


def calculate_stop_len(nonhours) -> str:
    ret = ""
    for idx, h in enumerate(nonhours):
        if idx + 1 < len(nonhours):
            if _getuneven(nonhours[idx + 1], nonhours[idx]):
                ret = _get_stopped_string(h)
                break
        elif idx + 1 == len(nonhours):
            ret = _get_stopped_string(h)
            break
    return ret


def _get_stopped_string(h) -> str:
    val = h + 1 if h + 1 < 24 else h + 1 - 24
    if len(str(val)) == 1:
        return f"Charging stopped until 0{val}:00"
    return f"Charging stopped until {val}:00"


def _getuneven(first, second) -> bool:
    if second > first:
        return first - (second - 24) != 1
    return first - second != 1


class PeaqMoneySensor(SensorBase, RestoreEntity):
    """Special sensor which is only created if priceaware is true"""

    def __init__(self, hub, entry_id):
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
        ret = await self.hub.async_request_sensor_data("prices_tomorrow", "non_hours", "dynamic_caution_hours",
                                                       "currency", "offsets", "average_nordpool_data", "use_cent",
                                                       "current_peak", "avg_kwh_price", "max_charge", "average_weekly",
                                                       "average_monthly")
        if ret is not None:
            self._state = await self.async_state_display(ret.get("non_hours"), ret.get("dynamic_caution_hours"))
            self._nonhours = await self.async_set_non_hours_display(ret.get("non_hours"), ret.get("prices_tomorrow"))
            self._dynamic_caution_hours = await self.async_set_caution_hours_display(ret.get("dynamic_caution_hours"))
            self._currency = ret.get("currency")
            self._offsets = ret.get("offsets", {})
            self._current_peak = ret.get("current_peak")
            self._max_charge = f"{ret.get('max_charge', '-')} kWh"
            self._average_nordpool_data = ret.get("average_nordpool_data", [])
            self._charge_permittance = await self.async_set_current_charge_permittance_display(ret.get("non_hours"),
                                                                                               ret.get(
                                                                                                   "dynamic_caution_hours"))

            self._avg_cost = await self.async_currency_translation(value=ret.get("avg_kwh_price"),
                                                                   currency=ret.get("currency"),
                                                                   use_cent=ret.get("use_cent"))

            self._average_nordpool = await self.async_currency_translation(value=ret.get("average_weekly"),
                                                                           currency=ret.get("currency"),
                                                                           use_cent=ret.get("use_cent"))
            self._average_data_current_month = await self.async_currency_translation(value=ret.get("average_monthly"),
                                                                                     currency=ret.get("currency"),
                                                                                     use_cent=ret.get("use_cent"))

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {
            "Non hours":                       self._nonhours,
            "Caution hours":                   self._dynamic_caution_hours,
            "Current hour charge permittance": self._charge_permittance,
            "Avg price per kWh":               self._avg_cost,
            "Max charge amount":               self._max_charge,
            "Nordpool average 7 days":         self._average_nordpool,
            "nordpool_average_this_month":     self._average_data_current_month,
            "Nordpool average data":           self._average_nordpool_data,
            "offsets":                         self._offsets
        }
        return attr_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        _LOGGER.debug("last state of %s = %s", self._attr_name, state)
        if state:
            # rr = [0.646, 0.909, 1.637, 2.085, 2.093, 1.385, 1.849, 1.803, 1.805, 1.634, 1.302, 1.079, 0.58, 0.815, 0.813, 1.219, 1.145, 0.417, 0.426, 0.736, 1.138, 1.04, 0.647, 0.519, 0.599, 0.433, 0.727, 0.898, 1.124, 1.476]
            # await self.hub.nordpool.async_import_average_data(rr)
            await self.hub.nordpool.async_import_average_data(state.attributes.get('Nordpool average data', 50))
            self._average_nordpool_data = list(state.attributes.get('Nordpool average data', 50))
            self._average_nordpool = f"{self.hub.nordpool.average_weekly} {self._currency}"
            self._average_data_current_month = f"{self.hub.nordpool.average_month} {self._currency}"
        else:
            self._average_nordpool = f"- {self._currency}"

    @staticmethod
    async def async_currency_translation(value, currency, use_cent: bool = False) -> str:
        match currency:
            case "EUR":
                ret = f"{value}¢" if use_cent else f"€ {value}"
            case "SEK":
                ret = f"{value} öre" if use_cent else f"{value} kr"
            case "NOK":
                ret = f"{value} øre" if use_cent else f"{value} kr"
            case _:
                ret = f"{value} {currency}"
        return ret

    @staticmethod
    async def async_set_non_hours_display(non_hours: list, prices_tomorrow: list) -> list:
        ret = []
        for i in non_hours:
            if i < datetime.now().hour and len(prices_tomorrow) > 0:
                ret.append(f"{str(i)}⁺¹")
            elif i >= datetime.now().hour:
                ret.append(str(i))
        return ret

    @staticmethod
    async def async_set_caution_hours_display(dynamic_caution_hours: dict) -> dict:
        ret = {}
        if len(dynamic_caution_hours) > 0:
            for h in dynamic_caution_hours:
                if h < datetime.now().hour:
                    hh = f"{h}⁺¹"
                else:
                    hh = h
                ret[hh] = f"{str((int(dynamic_caution_hours.get(h, 0) * 100)))}%"
        return ret

    @staticmethod
    async def async_set_current_charge_permittance_display(non_hours, dynamic_caution_hours) -> str:
        ret = 100
        hour = datetime.now().hour
        if hour in non_hours:
            ret = 0
        elif hour in dynamic_caution_hours.keys():
            ret = int(dynamic_caution_hours.get(hour) * 100)
        return f"{str(ret)}%"

    async def async_state_display(self, non_hours: list, dynamic_caution_hours: dict) -> str:
        hour = datetime.now().hour
        ret = CHARGING_ALLOWED.capitalize()
        if self.hub.hours.timer.is_override:  # todo: composition
            self._icon = "mdi:car-electric-outline"
            return self.hub.hours.timer.override_string  # todo: composition
        if hour in non_hours:
            self._icon = "mdi:car-clock"
            ret = calculate_stop_len(non_hours)
        elif hour in dynamic_caution_hours.keys():
            val = dynamic_caution_hours.get(hour)
            ret += f" at {int(val * 100)}% of peak"
        return ret
