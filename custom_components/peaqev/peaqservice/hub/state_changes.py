import logging
import time
from datetime import datetime

from custom_components.peaqev.peaqservice.util.constants import SMARTOUTLET

_LOGGER = logging.getLogger(__name__)

class StateChanges:
    latest_nordpool_update = 0
    latest_outlet_update = 0

    def __init__(self, hub):
        self._hub = hub

    async def update_sensor(self, entity, value):
        if self._hub.options.peaqev_lite is True:
            await self._update_sensor_lite(entity, value)
            update_session = False
        else:
            update_session = await self._update_sensor_regular(entity, value)

        if entity != self._hub.nordpool.nordpool_entity and (not self._hub.hours.is_initialized or time.time() - self.latest_nordpool_update > 60):
            """tweak to provoke nordpool to update more often"""
            self.latest_nordpool_update = time.time()
            await self._hub.nordpool.update_nordpool()
        if self._hub.charger.session_active and update_session:
            self._hub.charger.session.session_energy = self._hub.sensors.carpowersensor.value
            self._hub.charger.session.session_price = float(self._hub.nordpool.state)
        if self._hub.scheduler.schedule_created is True:
            self._hub.scheduler.update()
        if entity in self._hub.chargingtracker_entities and self._hub.is_initialized is True:
            await self._hub.charger.charge()

    async def _update_sensor_lite(self, entity, value) -> None:
        match entity:
            case self._hub.sensors.carpowersensor.entity:
                self._hub.sensors.carpowersensor.value = value
                await self._handle_outlet_updates()
                self._hub.sensors.chargerobject_switch.updatecurrent()
            case self._hub.sensors.chargerobject.entity:
                self._hub.sensors.chargerobject.value = value
            case self._hub.sensors.chargerobject_switch.entity:
                self._hub.sensors.chargerobject_switch.value = value
                self._hub.sensors.chargerobject_switch.updatecurrent()
                await self._handle_outlet_updates()
            case self._hub.sensors.current_peak.entity:
                self._hub.sensors.current_peak.value = value
            case self._hub.sensors.totalhourlyenergy.entity:
                self._hub.sensors.totalhourlyenergy.value = value
                self._hub.sensors.current_peak.value = self._hub.sensors.locale.data.query_model.observed_peak
                self._hub.sensors.locale.data.query_model.try_update(
                    new_val=float(value),
                    timestamp=datetime.now()
                )
            case self._hub.nordpool.nordpool_entity:
                await self._hub.nordpool.update_nordpool()

    async def _update_sensor_regular(self, entity, value) -> bool:
        update_session = False
        match entity:
            case self._hub.configpower_entity:
                self._hub.sensors.power.update(
                    carpowersensor_value=self._hub.sensors.carpowersensor.value,
                    config_sensor_value=value
                )
                update_session = True
            case self._hub.sensors.carpowersensor.entity:
                self._hub.sensors.carpowersensor.value = value
                self._hub.sensors.power.update(
                    carpowersensor_value=self._hub.sensors.carpowersensor.value,
                    config_sensor_value=None
                )
                update_session = True
                self._hub.sensors.chargerobject_switch.updatecurrent()
                await self._handle_outlet_updates()
            case self._hub.sensors.chargerobject.entity:
                self._hub.sensors.chargerobject.value = value
            case self._hub.sensors.chargerobject_switch.entity:
                self._hub.sensors.chargerobject_switch.value = value
                self._hub.sensors.chargerobject_switch.updatecurrent()
                await self._handle_outlet_updates()
            case self._hub.sensors.totalhourlyenergy.entity:
                self._hub.sensors.totalhourlyenergy.value = value
                self._hub.sensors.current_peak.value = self._hub.sensors.locale.data.query_model.observed_peak
                self._hub.sensors.locale.data.query_model.try_update(
                    new_val=float(value),
                    timestamp=datetime.now()
                )
            case self._hub.sensors.powersensormovingaverage.entity:
                self._hub.sensors.powersensormovingaverage.value = value
            case self._hub.sensors.powersensormovingaverage24.entity:
                self._hub.sensors.powersensormovingaverage24.value = value
            case self._hub.nordpool.nordpool_entity:
                await self._hub.nordpool.update_nordpool()
                update_session = True
        return update_session

    async def _handle_outlet_updates(self):
        old_state = self._hub.sensors.chargerobject.value
        if self._hub.chargertype.charger.domainname == SMARTOUTLET:
            if time.time() - self.latest_outlet_update < 10:
                return
            self.latest_outlet_update = time.time()
            if self._hub.sensors.carpowersensor.value > 0:
                self._hub.sensors.chargerobject.value = "charging"
            else:
                self._hub.sensors.chargerobject.value = "connected"
            if old_state != self._hub.sensors.chargerobject.value:
                _LOGGER.debug(f"smartoutlet is now {self._hub.sensors.chargerobject.value}")