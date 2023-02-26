import logging
from abc import abstractmethod
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class IStateChanges:
    latest_nordpool_update = 0
    latest_outlet_update = 0

    def __init__(self, hub):
        self._hub = hub

    async def update_sensor(self, entity, value):
        update_session = await self._update_sensor(entity, value)
        if self._hub.options.price.price_aware is True:
            if entity != self._hub.nordpool.nordpool_entity and (not self._hub.hours.is_initialized or time.time() - self.latest_nordpool_update > 60):
                """tweak to provoke nordpool to update more often"""
                self.latest_nordpool_update = time.time()
                await self._hub.nordpool.update_nordpool()
        await self._handle_sensor_attribute()
        if self._hub.charger.session_active and update_session and hasattr(self._hub.sensors, "carpowersensor"):
            self._hub.charger.session.session_energy = self._hub.sensors.carpowersensor.value
            if self._hub.options.price.price_aware is True:
                self._hub.charger.session.session_price = float(self._hub.nordpool.state)
        if self._hub.scheduler.schedule_created is True:
            self._hub.scheduler.update()
        if entity in self._hub.chargingtracker_entities and self._hub.is_initialized:
            await self._hub.charger.charge()

    @abstractmethod
    async def _update_sensor(self, entity, value) -> bool:
        pass

    @abstractmethod
    async def _handle_outlet_updates(self):
        pass

    async def _handle_sensor_attribute(self) -> None:
        if hasattr(self._hub.sensors, "carpowersensor"):
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

    async def _update_chargerobject_switch(self, value) -> None:
        self._hub.sensors.chargerobject_switch.value = value
        self._hub.sensors.chargerobject_switch.updatecurrent()
        await self._handle_outlet_updates()

    async def _update_total_energy_and_peak(self, value) -> None:
        self._hub.sensors.totalhourlyenergy.value = value
        self._hub.sensors.current_peak.value = self._hub.sensors.locale.data.query_model.observed_peak
        self._hub.sensors.locale.data.query_model.try_update(
            new_val=float(value),
            timestamp=datetime.now()
        )


import logging
import time
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import IStateChanges
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType

_LOGGER = logging.getLogger(__name__)


class StateChanges(IStateChanges):
    def __init__(self, hub):
        self._hub = hub
        super().__init__(hub)

    async def _update_sensor(self, entity, value) -> bool:
        update_session = False
        match entity:
            case self._hub.configpower_entity:
                self._hub.sensors.power.update(
                    carpowersensor_value=self._hub.sensors.carpowersensor.value,
                    config_sensor_value=value
                )
                update_session = True
                self._hub.power_canary.total_power = self._hub.sensors.power.total.value
            case self._hub.sensors.carpowersensor.entity:
                # if self._hub.sensors.carpowersensor.use_attribute:
                #     pass
                # else:
                #     self._hub.sensors.carpowersensor.value = value
                #     self._hub.sensors.power.update(
                #         carpowersensor_value=self._hub.sensors.carpowersensor.value,
                #         config_sensor_value=None
                #     )
                update_session = True
                # self._hub.sensors.chargerobject_switch.updatecurrent()
                # self._hub.power_canary.total_power = self._hub.sensors.power.total.value
                #await self._handle_outlet_updates()

        return update_session


class StateChangesLite(IStateChanges):
    def __init__(self, hub):
        self._hub = hub
        super().__init__(hub)

    async def _update_sensor(self, entity, value) -> bool:
        match entity:
            case self._hub.sensors.carpowersensor.entity:
                if self._hub.sensors.carpowersensor.use_attribute:
                    pass
                else:
                    self._hub.sensors.carpowersensor.value = value
                self._hub.sensors.chargerobject_switch.updatecurrent()
        return False

class StateChangesNoCharger(IStateChanges):
    def __init__(self, hub):
        self._hub = hub
        super().__init__(hub)

    async def _update_sensor(self, entity, value) -> bool:
        update_session = False
        match entity:
            case self._hub.configpower_entity:
                self._hub.sensors.power.update(
                    carpowersensor_value=0,
                    config_sensor_value=value
                )
                update_session = True
                self._hub.power_canary.total_power = self._hub.sensors.power.total.value
                update_session = True
        return update_session


class StateChanges2(IStateChanges):
    def __init__(self, hub):
        self._hub = hub
        self._funcs = {}

    def _execute(self, entity, value) -> None:
        try:
            self._funcs.get(entity)(value)
        except KeyError:
            pass

    def _set_value(self, func, val) -> None:
        func = val

    def _setup_powersensor_moving_average(self) -> None:
        self._funcs[self._hub.sensors.powersensormovingaverage.entity] = lambda x: self._set_value(self._hub.sensors.powersensormovingaverage.value, x)
        self._funcs[self._hub.sensors.powersensormovingaverage24.entity] = lambda x: self._set_value(self._hub.sensors.powersensormovingaverage24.value, x)

    def _setup_total_hourly_energy(self) -> None:
        self._funcs[self._hub.sensors.totalhourlyenergy.entity] = lambda x: self._update_total_energy_and_peak(x)

    def _setup_nordpool(self) -> None:
        self._funcs[self._hub.nordpool.nordpool_entity] = lambda x: self._hub.nordpool.update_nordpool()

    def _setup_chargerobject(self) -> None:
        self._funcs[self._hub.sensors.chargerobject.entity] = lambda x: self._set_value(self._hub.sensors.chargerobject.value, x)
        self._funcs[self._hub.sensors.chargerobject_switch.entity] = lambda x: self._update_chargerobject_switch(x)

    def _setup_carpowersensor(self) -> None:
        self._funcs[self._hub.sensors.carpowersensor.entity] = lambda x: self._set_carpowersensor_value(x)

    def _setup_carpowersensor_lite(self) -> None:
        self._funcs[self._hub.sensors.carpowersensor.entity] = lambda x: self._set_carpowersensor_value_lite(x)

    def _setup_carpowersensor_outlet(self) -> None:
        self._funcs[self._hub.sensors.carpowersensor.entity] = lambda x: self._handle_outlet_updates()

    def _setup_update_current(self) -> None:
        self._funcs[self._hub.sensors.carpowersensor.entity] = lambda x: self._hub.sensors.chargerobject_switch.updatecurrent()

    #not constructor methods
    def _set_carpowersensor_value(self, value) -> None:
        if self._hub.sensors.carpowersensor.use_attribute:
            pass
        else:
            self._hub.sensors.carpowersensor.value = value
            self._hub.sensors.power.update(
                carpowersensor_value=self._hub.sensors.carpowersensor.value,
                config_sensor_value=None
            )
            #self._hub.power_canary.total_power = self._hub.sensors.power.total.value

    def _set_carpowersensor_value_lite(self, value) -> None:
        if self._hub.sensors.carpowersensor.use_attribute:
            pass
        else:
            self._hub.sensors.carpowersensor.value = value
            #self._hub.power_canary.total_power = self._hub.sensors.power.total.value

    async def _handle_outlet_updates(self):
        if self._hub.chargertype.domainname is ChargerType.Outlet:
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

    def construct(self) -> None:
        if hasattr(self._hub.sensors, "carpowersensor"):
            if self._hub.chargertype.domainname is ChargerType.Outlet:
                self._setup_carpowersensor_outlet()
            elif self._hub.options.peaqev_lite:
                self._setup_carpowersensor_lite()
            else:
                self._setup_carpowersensor()
        if self._hub.options.price.price_aware:
            self._setup_nordpool()
        if not self._hub.options.peaqev_lite:
            self._setup_powersensor_moving_average()
        #if self._hub.chargertype.