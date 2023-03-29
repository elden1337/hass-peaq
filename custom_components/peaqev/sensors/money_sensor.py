import logging

from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.peaqev.peaqservice.util.constants import HOURCONTROLLER
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)


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
        ret = await self.hub.async_get_money_sensor_data()
        if ret is not None:
            self._state = ret.get("state")
            self._nonhours = ret.get("nonhours")
            self._dynamic_caution_hours = ret.get("cautionhours")
            self._currency = ret.get("currency")
            self._offsets = ret.get("offsets", {})
            self._current_peak = ret.get("current_peak")
            self._max_charge = f"{ret.get('max_charge', '-')} kWh"
            self._average_nordpool_data = ret.get("average_nordpool_data", [])
            self._charge_permittance = ret.get("charge_permittance")

            self._avg_cost = self.currency_translation(value=ret.get("avg_kwh_price"),
                                                       currency=ret.get("currency"),
                                                       use_cent=ret.get("use_cent"))

            self._average_nordpool = self.currency_translation(value=ret.get("average_weekly"),
                                                               currency=ret.get("currency"),
                                                               use_cent=ret.get("use_cent"))
            self._average_data_current_month = self.currency_translation(value=ret.get("average_monthly"),
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
            rr = [0.646, 0.909, 1.637, 2.085, 2.093, 1.385, 1.849, 1.803, 1.805, 1.634, 1.302, 1.079, 0.58, 0.815, 0.813, 1.219, 1.145, 0.417, 0.426, 0.736, 1.138, 1.04, 0.647, 0.519, 0.599, 0.433, 0.727, 0.898, 1.124, 1.476]
            await self.hub.nordpool.async_import_average_data(rr)
            #await self.hub.nordpool.async_import_average_data(state.attributes.get('Nordpool average data', 50))
            #self._average_nordpool_data = list(state.attributes.get('Nordpool average data', 50))
            self._average_nordpool = f"{self.hub.nordpool.average_weekly} {self._currency}"
            self._average_data_current_month = f"{self.hub.nordpool.average_month} {self._currency}"
        else:
            self._average_nordpool = f"- {self._currency}"

    @staticmethod
    def currency_translation(value, currency, use_cent: bool = False) -> str:
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
