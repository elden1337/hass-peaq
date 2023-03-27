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

    def update(self) -> None:
        if self.hub.is_initialized:
            self._state = self.hub.chargecontroller.state_display_model  # todo: composition
            self._nonhours = self.hub.chargecontroller.non_hours_display_model  # todo: composition
            self._dynamic_caution_hours = self.hub.chargecontroller.caution_hours_display_model  # todo: composition
            self._currency = self.hub.nordpool.currency  # todo: composition
            self._offsets = self.hub.hours.offsets if self.hub.hours.offsets is not None else {}  # todo: composition
            self._current_peak = self.hub.sensors.current_peak.value  # todo: composition
            self._avg_cost = self.currency_translation(value=self.hub.hours.get_average_kwh_price(),
                                                       currency=self._currency,
                                                       use_cent=self.hub.nordpool.model.use_cent)  # todo: composition
            self._max_charge = f"{self.hub.hours.get_total_charge()} kWh"  # todo: composition
            self._average_nordpool = self.currency_translation(value=self.hub.nordpool.average_weekly,
                                                               currency=self._currency,
                                                               use_cent=self.hub.nordpool.model.use_cent)  # todo: composition
            self._average_data_current_month = self.currency_translation(value=self.hub.nordpool.average_month,
                                                                         currency=self._currency,
                                                                         use_cent=self.hub.nordpool.model.use_cent)  # todo: composition
            self._average_nordpool_data = self.hub.nordpool.average_data  # todo: composition
            self._charge_permittance = self.hub.chargecontroller.current_charge_permittance_display_model  # todo: composition

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
            await self.hub.nordpool.import_average_data(state.attributes.get('Nordpool average data', 50))
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
