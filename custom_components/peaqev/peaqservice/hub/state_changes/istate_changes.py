import logging
import time
from abc import abstractmethod
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class IStateChanges:
    latest_nordpool_update = 0
    latest_outlet_update = 0

    def __init__(self, hub):
        self.hub = hub

    async def update_sensor(self, entity, value):
        update_session = await self._update_sensor(entity, value)
        _ = await self.hub.chargecontroller.get_status()
        if self.hub.options.price.price_aware:
            if entity != self.hub.nordpool.nordpool_entity and (not self.hub.hours.is_initialized or time.time() - self.latest_nordpool_update > 60):
                """tweak to provoke nordpool to update more often"""
                self.latest_nordpool_update = time.time()
                await self.hub.nordpool.update_nordpool()
        await self._handle_sensor_attribute()
        if self.hub.charger.session_active and update_session and hasattr(self.hub.sensors, "carpowersensor"):
            self.hub.charger.session.session_energy = self.hub.sensors.carpowersensor.value
            if self.hub.options.price.price_aware:
                self.hub.charger.session.session_price = float(self.hub.nordpool.state)
        if self.hub.scheduler.schedule_created:
            self.hub.scheduler.update()
        if entity in self.hub.chargingtracker_entities and self.hub.is_initialized:
            await self.hub.charger.charge()

    @abstractmethod
    async def _update_sensor(self, entity, value) -> bool:
        pass

    @abstractmethod
    async def _handle_outlet_updates(self):
        pass

    async def _handle_sensor_attribute(self) -> None:
        if hasattr(self.hub.sensors, "carpowersensor"):
            if self.hub.sensors.carpowersensor.use_attribute:
                entity = self.hub.sensors.carpowersensor
                try:
                    val = self.hub.hass.states.get(entity.entity).attributes.get(entity.attribute)
                    if val is not None:
                        self.hub.sensors.carpowersensor.value = val
                        self.hub.sensors.power.update(
                            carpowersensor_value=self.hub.sensors.carpowersensor.value,
                            config_sensor_value=None
                        )
                    return
                except Exception as e:
                    _LOGGER.debug(f"Unable to get attribute-state for {entity.entity}|{entity.attribute}. {e}")

    async def _update_chargerobject_switch(self, value) -> None:
        self.hub.sensors.chargerobject_switch.value = value
        self.hub.sensors.chargerobject_switch.updatecurrent()
        await self._handle_outlet_updates()

    async def _update_total_energy_and_peak(self, value) -> None:
        self.hub.sensors.totalhourlyenergy.value = value
        self.hub.sensors.current_peak.value = self.hub.sensors.locale.data.query_model.observed_peak
        self.hub.sensors.locale.data.query_model.try_update(
            new_val=float(value),
            timestamp=datetime.now()
        )