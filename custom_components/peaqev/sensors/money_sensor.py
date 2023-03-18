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

        self._initialized = False
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
        self._charge_permittance = None
        self._offsets = {}
        self._average_nordpool_data = []

    @property
    def state(self):
        return self.hub.chargecontroller.state_display_model  #todo: composition

    @property
    def icon(self) -> str:
        return "mdi:car-clock"

    def update(self) -> None:
        if self._initialized:
            _non = self.hub.chargecontroller.non_hours_display_model  #todo: composition
            if self._nonhours != _non:
                self._nonhours = _non
                _LOGGER.debug(f"Updating frontend nonhours with {_non}. The params we got were: adj-avg:{self.hub.hours.adjusted_average}, monthly-avg:{self.hub.hours._core.model.options.absolute_top_price}")
            self._dynamic_caution_hours = self.hub.chargecontroller.caution_hours_display_model  #todo: composition
            self._currency = self.hub.nordpool.currency  #todo: composition
            self._offsets = self.hub.hours.offsets if self.hub.hours.offsets is not None else {}  #todo: composition
            self._current_peak = self.hub.sensors.current_peak.value  #todo: composition
            self._avg_cost = f"{self.hub.hours.get_average_kwh_price()} {self._currency}"  #todo: composition
            self._max_charge = f"{self.hub.hours.get_total_charge()} kWh"  #todo: composition
            self._average_nordpool = f"{self.hub.nordpool.average_weekly} {self._currency}"  #todo: composition
            self._average_data_current_month = f"{self.hub.nordpool.average_month} {self._currency}"  #todo: composition
            self._average_nordpool_data = self.hub.nordpool.average_data  #todo: composition
            self._charge_permittance = self.hub.chargecontroller.current_charge_permittance_display_model  #todo: composition

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
            "offsets": self._offsets
        }
        return attr_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            await self.hub.nordpool.import_average_data(state.attributes.get('Nordpool average data', 50))
            _LOGGER.debug("successfully awaited import_average data")
            self._average_nordpool = f"{self.hub.nordpool.average_weekly} {self._currency}"
            self._average_data_current_month = f"{self.hub.nordpool.average_month} {self._currency}"
            self._initialized = True
        else:
            self._average_nordpool = f"- {self._currency}"
            self._initialized = True