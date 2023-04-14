import logging
import time
from abc import abstractmethod
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class IStateChanges:
    latest_nordpool_update = 0
    latest_outlet_update = 0
    latest_chargecontroller_update = 0

    def __init__(self, hub):
        self.hub = hub

    async def async_update_sensor(self, entity, value):
        update_session = await self.async_update_sensor_internal(entity, value)
        if time.time() - self.latest_chargecontroller_update > 3:
            self.latest_chargecontroller_update = time.time()
            await self.hub.chargecontroller.async_set_status()
            if not self.hub.override_max_charge:  # todo: 247
                await self.hub.async_reset_max_charge_sensor()  # todo: 247
        if self.hub.options.price.price_aware:
            if entity != self.hub.nordpool.nordpool_entity and (
                not self.hub.hours.is_initialized
                or time.time() - self.latest_nordpool_update > 60
            ):
                """tweak to provoke nordpool to update more often"""
                self.latest_nordpool_update = time.time()
                await self.hub.nordpool.async_update_nordpool()
        await self.async_handle_sensor_attribute()
        await self.async_update_session_parameters(update_session)
        if entity in self.hub.chargingtracker_entities and self.hub.is_initialized:
            await self.hub.chargecontroller.charger.async_charge()

    async def async_update_session_parameters(self, update_session: bool) -> None:
        if all(
            [
                self.hub.chargecontroller.charger.session_active,
                update_session,
                hasattr(self.hub.sensors, "carpowersensor"),
            ]
        ):
            setattr(
                self.hub.chargecontroller.charger.session,
                "session_energy",
                getattr(self.hub.sensors.carpowersensor, "value"),
            )
            if self.hub.options.price.price_aware:
                self.hub.chargecontroller.charger.session.session_price = float(
                    self.hub.nordpool.state
                )
                if getattr(self.hub.hours.scheduler, "schedule_created", False):
                    await self.hub.hours.scheduler.async_update_facade()

    async def async_handle_sensor_attribute(self) -> None:
        if hasattr(self.hub.sensors, "carpowersensor"):
            if self.hub.sensors.carpowersensor.use_attribute:
                entity = self.hub.sensors.carpowersensor
                try:
                    val = self.hub.hass.states.get(entity.entity).attributes.get(
                        entity.attribute
                    )
                    if val is not None:
                        self.hub.sensors.carpowersensor.value = val
                        await self.hub.sensors.power.async_update(
                            carpowersensor_value=self.hub.sensors.carpowersensor.value,
                            config_sensor_value=None,
                        )
                    return
                except Exception as e:
                    _LOGGER.debug(
                        f"Unable to get attribute-state for {entity.entity}|{entity.attribute}. {e}"
                    )

    async def async_update_chargerobject_switch(self, value) -> None:
        self.hub.sensors.chargerobject_switch.value = value
        await self.hub.sensors.chargerobject_switch.async_updatecurrent()
        await self.async_handle_outlet_updates()

    async def async_update_total_energy_and_peak(self, value) -> None:
        self.hub.sensors.totalhourlyenergy.value = value
        self.hub.sensors.current_peak.value = (
            self.hub.sensors.locale.data.query_model.observed_peak
        )
        self.hub.sensors.locale.data.query_model.try_update(
            new_val=float(value), timestamp=datetime.now()
        )
        if self.hub.options.price.price_aware:
            await self.hub.hours.async_update_max_min(self.hub.max_charge)

    @abstractmethod
    async def async_update_sensor_internal(self, entity, value) -> bool:
        pass

    @abstractmethod
    async def async_handle_outlet_updates(self):
        pass
