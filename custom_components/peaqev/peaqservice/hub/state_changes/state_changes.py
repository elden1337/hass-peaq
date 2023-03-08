import logging
import time

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import IStateChanges

_LOGGER = logging.getLogger(__name__)


class StateChanges(IStateChanges):
    def __init__(self, hub):
        self.hub = hub
        super().__init__(hub)

    async def _update_sensor(self, entity, value) -> bool:
        update_session = False
        match entity:
            case self.hub.options.powersensor:
                self.hub.sensors.power.update(
                    carpowersensor_value=self.hub.sensors.carpowersensor.value,
                    config_sensor_value=value
                )
                update_session = True
                self.hub.power_canary.total_power = self.hub.sensors.power.total.value
            case self.hub.sensors.carpowersensor.entity:
                if self.hub.sensors.carpowersensor.use_attribute:
                    pass
                else:
                    self.hub.sensors.carpowersensor.value = value
                    self.hub.sensors.power.update(
                        carpowersensor_value=self.hub.sensors.carpowersensor.value,
                        config_sensor_value=None
                    )
                update_session = True
                self.hub.sensors.chargerobject_switch.updatecurrent()
                self.hub.power_canary.total_power = self.hub.sensors.power.total.value
                await self._handle_outlet_updates()
            case self.hub.sensors.chargerobject.entity:
                self.hub.set_chargerobject_value(value)
            case self.hub.sensors.chargerobject_switch.entity:
                await self._update_chargerobject_switch(value)
            case self.hub.sensors.totalhourlyenergy.entity:
                await self._update_total_energy_and_peak(value)
            case self.hub.sensors.powersensormovingaverage.entity:
                self.hub.sensors.powersensormovingaverage.value = value
            case self.hub.sensors.powersensormovingaverage24.entity:
                self.hub.sensors.powersensormovingaverage24.value = value
            case self.hub.nordpool.nordpool_entity:
                await self.hub.nordpool.update_nordpool()
                update_session = True
        return update_session
    
    async def _handle_outlet_updates(self):
        if self.hub.chargertype.domainname is ChargerType.Outlet:
            old_state = self.hub.get_chargerobject_value()
            if time.time() - self.latest_outlet_update < 10:
                return
            self.latest_outlet_update = time.time()
            if self.hub.sensors.carpowersensor.value > 0:
                self.hub.set_chargerobject_value("charging")
            else:
                self.hub.set_chargerobject_value("connected")
            if old_state != self.hub.get_chargerobject_value():
                _LOGGER.debug(f"smartoutlet is now {self.hub.get_chargerobject_value()}")


class StateChangesLite(IStateChanges):
    def __init__(self, hub):
        self.hub = hub
        super().__init__(hub)

    async def _update_sensor(self, entity, value) -> bool:
        match entity:
            case self.hub.sensors.carpowersensor.entity:
                if self.hub.sensors.carpowersensor.use_attribute:
                    pass
                else:
                    self.hub.sensors.carpowersensor.value = value
                    await self._handle_outlet_updates()
                    self.hub.sensors.chargerobject_switch.updatecurrent()
            case self.hub.sensors.chargerobject.entity:
                self.hub.set_chargerobject_value(value)
            case self.hub.sensors.chargerobject_switch.entity:
                await self._update_chargerobject_switch(value)
            case self.hub.sensors.current_peak.entity:
                self.hub.sensors.current_peak.value = value
            case self.hub.sensors.totalhourlyenergy.entity:
                await self._update_total_energy_and_peak(value)
            case self.hub.nordpool.nordpool_entity:
                await self.hub.nordpool.update_nordpool()
        return False
    
    async def _handle_outlet_updates(self):
        if self.hub.chargertype.domainname is ChargerType.Outlet:
            old_state = self.hub.get_chargerobject_value()
            if time.time() - self.latest_outlet_update < 10:
                return
            self.latest_outlet_update = time.time()
            if self.hub.sensors.carpowersensor.value > 0:
                self.hub.set_chargerobject_value("charging")
            else:
                self.hub.set_chargerobject_value("connected")
            if old_state != self.hub.get_chargerobject_value():
                _LOGGER.debug(f"smartoutlet is now {self.hub.get_chargerobject_value()}")


class StateChangesNoCharger(IStateChanges):
    def __init__(self, hub):
        self.hub = hub
        super().__init__(hub)

    async def _update_sensor(self, entity, value) -> bool:
        update_session = False
        match entity:
            case self.hub.options.powersensor:
                self.hub.sensors.power.update(
                    carpowersensor_value=0,
                    config_sensor_value=value
                )
                update_session = True
                self.hub.power_canary.total_power = self.hub.sensors.power.total.value
            case self.hub.sensors.totalhourlyenergy.entity:
                await self._update_total_energy_and_peak(value)
            case self.hub.sensors.powersensormovingaverage.entity:
                _LOGGER.debug(f"trying to update powersensormovingaverage with {value}")
                self.hub.sensors.powersensormovingaverage.value = value
            case self.hub.sensors.powersensormovingaverage24.entity:
                self.hub.sensors.powersensormovingaverage24.value = value
            case self.hub.nordpool.nordpool_entity:
                await self.hub.nordpool.update_nordpool()
                update_session = True
        return update_session

class StateChangesLiteNoCharger(IStateChanges):
    def __init__(self, hub):
        self.hub = hub
        super().__init__(hub)

    async def _update_sensor(self, entity, value) -> bool:

        match entity:
            case self.hub.sensors.totalhourlyenergy.entity:
                await self._update_total_energy_and_peak(value)
            case self.hub.nordpool.nordpool_entity:
                await self.hub.nordpool.update_nordpool()
        return False


