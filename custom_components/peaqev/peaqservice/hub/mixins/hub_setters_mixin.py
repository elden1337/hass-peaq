import logging

from custom_components.peaqev.peaqservice.hub.observer.models.observer_types import ObserverTypes

_LOGGER = logging.getLogger(__name__)

class HubSettersMixin:
    async def async_set_init_dict(self, init_dict):
        await self.sensors.locale.data.query_model.peaks.async_set_init_dict(
            init_dict
        )
        try:
            ff = getattr(self.sensors.locale.data.query_model.peaks, "export_peaks", {})
            _LOGGER.debug(f"intialized_peaks: {ff}")
        except Exception:
            pass


    async def async_set_chargerobject_value(self, value) -> None:
        if hasattr(self.sensors, "chargerobject"):
            setattr(self.sensors.chargerobject, "value", value)


    async def async_update_prices(self, prices: list) -> None:
        if self.options.price.price_aware:
            await self.hours.async_update_prices(prices[0], prices[1])
            if self.max_min_controller.is_on:
                await self.hours.async_update_max_min(
                    max_charge=self.max_min_controller.max_charge,
                    limiter=self.max_min_controller.max_min_limiter,
                    car_connected=self.chargecontroller.connected,
                    session_energy=self.chargecontroller.session.session_energy,
                )


    async def async_update_average_monthly_price(self, val) -> None:
        if self.options.price.price_aware and isinstance(val, float):
            await self.hours.async_update_top_price(val)


    async def async_update_adjusted_average(self, val) -> None:
        if self.options.price.price_aware and isinstance(val, float):
            await self.hours.async_update_adjusted_average(val)


    async def async_update_charger_done(self, val):
        setattr(self.sensors.charger_done, "value", bool(val))


    async def async_update_charger_enabled(self, val):
        await self.observer.async_broadcast(ObserverTypes.UpdateLatestChargerStart)
        if hasattr(self.sensors, "charger_enabled"):
            setattr(self.sensors.charger_enabled, "value", bool(val))
        else:
            raise Exception("Peaqev cannot function without a charger_enabled entity")