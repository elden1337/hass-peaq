import logging
import time
from datetime import datetime
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from peaqevcore.models.hub.hubmember import HubMember

_LOGGER = logging.getLogger(__name__)

from abc import ABC, abstractmethod

class IStateChanges(ABC):
    latest_nordpool_update: int = 0
    latest_outlet_update: int = 0
    update_session: bool = False

    async def update_sensor(self, entity, value):
        await self._update_sensor(entity, value)
        if self._hub.options.price.price_aware: #factory-priceaware
            if entity != self._hub.nordpool.nordpool_entity and (not self._hub.hours.is_initialized or time.time() - self.latest_nordpool_update > 60):
                """tweak to provoke nordpool to update more often"""
                self.latest_nordpool_update = time.time()
                await self._hub.nordpool.update_nordpool()
        await self._handle_sensor_attribute()
        if self._hub.charger.session_active and self.update_session: #observer?
            self._hub.charger.session.session_energy = self._hub.sensors.carpowersensor.value
            if self._hub.options.price.price_aware: #factory-priceaware
                self._hub.charger.session.session_price = float(self._hub.nordpool.state)
        if self._hub.scheduler.schedule_created:
            self._hub.scheduler.update()
        if entity in self._hub.chargingtracker_entities and self._hub.is_initialized:
            await self._hub.charger.charge()

    @abstractmethod
    async def _update_sensor(self, entity, value) -> None:
        pass

    def _set_val(func, val):
        if isinstance(func, HubMember): 
            func.value = val
        else:
            func(val)

    async def _update_total_energy_and_peak(self, value) -> None:
        self._hub.sensors.totalhourlyenergy.value = value
        self._hub.sensors.current_peak.value = self._hub.sensors.locale.data.query_model.observed_peak
        self._hub.sensors.locale.data.query_model.try_update(
            new_val=float(value),
            timestamp=datetime.now()
        )

    async def _update_chargerobject_switch(self, value) -> None:
        self._hub.sensors.chargerobject_switch.value = value
        self._hub.sensors.chargerobject_switch.updatecurrent()
        await self._handle_outlet_updates()

    async def _handle_outlet_updates(self):
        if self._hub.chargertype.type is ChargerType.Outlet:
            old_state = self._hub.sensors.chargerobject.value
            if time.time() - self.latest_outlet_update < 10:
                return
            self.latest_outlet_update = time.time()
            if self._hub.sensors.carpowersensor.value > 0:
                self._hub.sensors.chargerobject.value = "charging"
            else:
                self._hub.sensors.chargerobject.value = "connected"
            if old_state != self._hub.sensors.chargerobject.value:
                _LOGGER.debug(f"smartoutlet is now {self._hub.sensors.chargerobject.value}")


class StateChanges(IStateChanges):
    def __init__(self, hub):
        self._hub = hub

    async def _update_carpowersensor(self, value):
        if self._hub.sensors.carpowersensor.use_attribute:
            pass
        else:
            self._hub.sensors.carpowersensor.value = value
            self._hub.sensors.power.update(
                carpowersensor_value=self._hub.sensors.carpowersensor.value,
                config_sensor_value=None
            )
        self.update_session = True
        self._hub.sensors.chargerobject_switch.updatecurrent()
        self._hub.power_canary.total_power = self._hub.sensors.power.total.value
        await self._handle_outlet_updates()

    async def _update_configpower(self, value):
        self._hub.sensors.power.update(
                    carpowersensor_value=self._hub.sensors.carpowersensor.value,
                    config_sensor_value=value
                )
        self.update_session = True
        self._hub.power_canary.total_power = self._hub.sensors.power.total.value

    async def _update_sensor(self, entity, value) -> None:
        self.update_session = False
        look = {
            self._hub.sensors.totalhourlyenergy.entity: lambda a: await self._update_total_energy_and_peak(a),
            self._hub.sensors.chargerobject.entity: self._hub.sensors.chargerobject,
            self._hub.sensors.powersensormovingaverage.entity: self._hub.sensors.powersensormovingaverage,
            self._hub.sensors.powersensormovingaverage24.entity: self._hub.sensors.powersensormovingaverage24,
            self._hub.sensors.chargerobject_switch.entity: lambda a: await self._update_chargerobject_switch(a),
            self._hub.configpower_entity: lambda a: await self._update_configpower(a),
            self._hub.sensors.carpowersensor.entity: lambda a: await self._update_carpowersensor(a)
        }

        self._set_val(look[entity], value)

        match entity:
            case self._hub.nordpool.nordpool_entity:
                await self._hub.nordpool.update_nordpool()
                self.update_session = True

    async def _handle_sensor_attribute(self) -> None:
        if self._hub.sensors.carpowersensor.use_attribute:
            entity = self._hub.sensors.carpowersensor
            try:
                val = self._hub.hass.states.get(entity.entity).attributes.get(entity.attribute)
                if val is not None:
                    self._hub.sensors.carpowersensor.value = val
                    self._hub.sensors.power.update(
                        carpowersensor_value=self._hub.sensors.carpowersensor.value,
                        config_sensor_value=None
                    )
                return
            except Exception as e:
                _LOGGER.debug(f"Unable to get attribute-state for {entity.entity}|{entity.attribute}. {e}")
    

class StateChangesLite(IStateChanges):
    def __init__(self, hub):
        self._hub = hub

    async def _update_carpowersensor(self, value) -> None:
        if self._hub.sensors.carpowersensor.use_attribute:
            return
        else:
            self._hub.sensors.carpowersensor.value = value
            await self._handle_outlet_updates()
            self._hub.sensors.chargerobject_switch.updatecurrent()

    async def _update_sensor(self, entity, value) -> None:
        look = {
            self._hub.sensors.chargerobject.entity: self._hub.sensors.chargerobject,
            self._hub.sensors.chargerobject_switch.entity: lambda a: await self._update_chargerobject_switch(a),
            self._hub.sensors.current_peak.entity: self._hub.sensors.current_peak,
            self._hub.sensors.totalhourlyenergy.entity: lambda a: await self._update_total_energy_and_peak(a),
            self._hub.nordpool.nordpool_entity: lambda: await self._hub.nordpool.update_nordpool(),
            self._hub.sensors.carpowersensor.entity: lambda a: await self._update_carpowersensor(a)
        }
        self._set_val(look[entity], value)


class StateChangesFactory:
    @staticmethod
    def create(hub) -> IStateChanges:
        if hub.options.peaqev_lite:
            return StateChangesLite(hub)
        return StateChanges(hub)    