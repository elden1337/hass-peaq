import logging
from datetime import datetime

from custom_components.peaqev.peaqservice.hub.const import LookupKeys
from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.hub.max_min_controller import \
    IMaxMinController
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade
from custom_components.peaqev.peaqservice.util.schedule_options_handler import \
    SchedulerOptionsHandler

_LOGGER = logging.getLogger(__name__)


class PriceAwareHub(HomeAssistantHub):
    def __init__(
            self,
            hass: IHomeAssistantFacade,
            options: HubOptions,
            domain: str,
            observer: IObserver,
            max_min_controller: IMaxMinController,
            scheduler_options_handler: SchedulerOptionsHandler
    ):
        super().__init__(hass=hass, options=options, domain=domain, observer=observer)
        self.max_min_controller = max_min_controller
        self.scheduler_options_handler = scheduler_options_handler
        self.observer.add('session energy', self.sessionenergyy)  #todo: move out of here when observer transformed.

    @property
    def current_peak_dynamic(self):
        """Dynamically calculated peak to adhere to caution-hours"""
        if self.hours.scheduler.active:
            return self.sensors.current_peak.observed_peak
        dynamic_caution_hours: dict = self._request_sensor_lookup().get(LookupKeys.DYNAMIC_CAUTION_HOURS, {})()
        if len(dynamic_caution_hours) > 0:
            if self.now_is_caution_hour() and not getattr(self.hours.timer, 'is_override', False):
                return self.sensors.current_peak.observed_peak * dynamic_caution_hours.get(
                    datetime.now().replace(minute=0, second=0, microsecond=0), 1)
        return self.sensors.current_peak.observed_peak

    async def async_is_caution_hour(self) -> bool:
        return False

    async def async_update_spotprice(self) -> None:
        await self.spotprice.async_update_spotprice()

    @property
    def sessionenergyy(self):  #todo: move out of here when observer transformed.
        return self.chargecontroller.session.session_energy

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
            _LOGGER.error(f'Unable to calculate watt cost. Exception: {e}')
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

    def _check_max_min_total_charge(self, ret: dict) -> None:
        if 'max_charge' in ret.keys():
            self.max_min_controller._original_total_charge = ret['max_charge'][0]
            # todo: 247

    async def async_update_max_min(self, keys) -> None:
        await self.hours.async_update_max_min(
            max_charge=keys.get('max_charge', 0),
            limiter=keys.get('limiter', 0),
            session_energy=self.chargecontroller.session.session_energy,
            car_connected=self.chargecontroller.connected
        )
