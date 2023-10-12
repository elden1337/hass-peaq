import logging
from datetime import datetime

from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.hub.max_min_controller import \
    MaxMinController
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions

_LOGGER = logging.getLogger(__name__)

class PriceAwareHub(HomeAssistantHub):
    def __init__(self, hass: HomeAssistant, options: HubOptions, domain: str):
        super().__init__(hass, options, domain)
        self.max_min_controller = MaxMinController(self)

    @property
    def current_peak_dynamic(self):
        """Dynamically calculated peak to adhere to caution-hours"""
        if len(self.dynamic_caution_hours) > 0:
            if self.now_is_caution_hour() and not getattr(self.hours.timer, "is_override", False):
                return (
                        self.sensors.current_peak.value
                        * self.dynamic_caution_hours[datetime.now().hour]
                )
        return self.sensors.current_peak.value

    async def async_is_caution_hour(self) -> bool:
        return False

    async def async_update_spotprice(self) -> None:
        await self.spotprice.async_update_spotprice()


    @property
    def watt_cost(self) -> int:
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

    async def async_update_prices(self, prices: list) -> None:
        await self.hours.async_update_prices(prices[0], prices[1])
        if self.max_min_controller.is_on:
            await self.hours.async_update_max_min(
                max_charge=self.max_min_controller.max_charge,
                limiter=self.max_min_controller.max_min_limiter,
                car_connected=self.chargecontroller.connected,
                session_energy=self.chargecontroller.session.session_energy,
            )

    async def async_update_average_monthly_price(self, val) -> None:
        if isinstance(val, float):
            await self.hours.async_update_top_price(val)

    async def async_update_adjusted_average(self, val) -> None:
        if isinstance(val, float):
            await self.hours.async_update_adjusted_average(val)

    def _check_max_min_total_charge(self, ret:dict) -> None:
        if "max_charge" in ret.keys():
            self.max_min_controller._original_total_charge = ret["max_charge"][0]
            # todo: 247
