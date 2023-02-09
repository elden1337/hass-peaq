import logging
from datetime import datetime

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
        self._avg_cost = None
        self._max_charge = None
        self._average_nordpool = None
        self._average_data_current_month = None
        self._offsets = {}
        self._average_nordpool_data = []

    @property
    def state(self):
        return self._hub.chargecontroller.state_display_model

    @property
    def icon(self) -> str:
        return "mdi:car-clock"

    def update(self) -> None:
        self._nonhours = self._hub.chargecontroller.non_hours_display_model
        self._dynamic_caution_hours = self._hub.chargecontroller.caution_hours_display_model
        self._currency = self._hub.nordpool.currency
        self._offsets = self._hub.hours.offsets if self._hub.hours.offsets is not None else {}
        self._current_peak = self._hub.sensors.current_peak.value
        self._avg_cost = f"{self._hub.hours.get_average_kwh_price()} {self._currency}"
        self._max_charge = f"{self._hub.hours.get_total_charge()} kWh"
        self._average_nordpool = f"{self._hub.nordpool.get_average(7)} {self._currency}"
        self._average_data_current_month = f"{self._hub.nordpool.get_average(datetime.now().day)} {self._currency}"
        self._average_nordpool_data = self._hub.nordpool.average_data

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {
            "Non hours": self._nonhours,
            "Caution hours": self._dynamic_caution_hours,
            "Current hour charge permittance": self._hub.chargecontroller.current_charge_permittance_display_model,
            "Avg price per kWh": self._avg_cost,
            "Max charge amount": self._max_charge,
            "Nordpool average 7 days": self._average_nordpool,
            "Nordpool average this month": self._average_data_current_month,
            "Nordpool average data": self._average_nordpool_data,
            "offsets": self._offsets
        }
        return attr_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            self._hub.nordpool.import_average_data(state.attributes.get('Nordpool average data', 50))
            self._average_nordpool = f"{self._hub.nordpool.get_average(7)} {self._currency}"
        else:
            self._average_nordpool = f"- {self._currency}"
