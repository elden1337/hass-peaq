from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
import logging

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import \
    IStateChanges

_LOGGER = logging.getLogger(__name__)


class StateChanges(IStateChanges):
    def __init__(self, hub: HomeAssistantHub):
        self.hub = hub
        super().__init__(hub)

    async def async_update_sensor_internal(self, entity, value) -> bool:
        try:
            update_session = False
            match entity:
                case self.hub.options.powersensor:
                    await self.hub.sensors.power.async_update(
                        carpowersensor_value=self.hub.sensors.carpowersensor.value,
                        config_sensor_value=value,
                    )
                    update_session = True
                    self.hub.power.power_canary.total_power = (
                        self.hub.sensors.power.total.value
                    )
                case self.hub.sensors.carpowersensor.entity:
                    if self.hub.sensors.carpowersensor.use_attribute:
                        pass
                    else:
                        self.hub.sensors.carpowersensor.value = value
                        await self.hub.sensors.power.async_update(
                            carpowersensor_value=self.hub.sensors.carpowersensor.value,
                            config_sensor_value=None,
                        )
                    update_session = True
                    #self.hub.sensors.amp_meter.update()
                    self.hub.power.power_canary.total_power = (
                        self.hub.sensors.power.total.value
                    )
                    await self.async_handle_outlet_updates()
                case self.hub.sensors.chargerobject.entity:
                    await self.hub.async_set_chargerobject_value(value)
                case self.hub.sensors.chargerobject_switch.entity:
                    await self.async_update_chargerobject_switch(value)
                case self.hub.sensors.totalhourlyenergy.entity:
                    await self.async_update_total_energy_and_peak(value)
                case self.hub.sensors.powersensormovingaverage.entity:
                    self.hub.sensors.powersensormovingaverage.value = value
                case self.hub.sensors.powersensormovingaverage24.entity:
                    self.hub.sensors.powersensormovingaverage24.value = value
                case self.hub.nordpool.nordpool_entity:
                    if self.hub.options.price.price_aware:
                        await self.hub.nordpool.async_update_nordpool()
                        update_session = True
            return update_session
        except Exception as e:
            _LOGGER.error(f"async_update_sensor_internal for {entity}: {e}")
            return False

    async def async_handle_outlet_updates(self):
        if self.hub.chargertype.domainname is ChargerType.Outlet:
            old_state = await self.hub.async_request_sensor_data("chargerobject_value")
            if not self.latest_outlet_update.is_timeout():
                return
            self.latest_outlet_update.update()
            if self.hub.sensors.carpowersensor.value > 0:
                await self.hub.async_set_chargerobject_value("charging")
            else:
                await self.hub.async_set_chargerobject_value("connected")
            if old_state != await self.hub.async_request_sensor_data(
                "chargerobject_value"
            ):
                _LOGGER.debug(
                    f"smartoutlet is now {await self.hub.async_request_sensor_data('chargerobject_value')}"
                )


class StateChangesLite(IStateChanges):
    def __init__(self, hub):
        self.hub = hub
        super().__init__(hub)

    async def async_update_sensor(self, entity, value) -> bool:
        match entity:
            case self.hub.sensors.carpowersensor.entity:
                if self.hub.sensors.carpowersensor.use_attribute:
                    pass
                else:
                    self.hub.sensors.carpowersensor.value = value
                    await self._handle_outlet_updates()
                    #self.hub.sensors.amp_meter.update()
            case self.hub.sensors.chargerobject.entity:
                await self.hub.async_set_chargerobject_value(value)
            case self.hub.sensors.chargerobject_switch.entity:
                await self.async_update_chargerobject_switch(value)
            case self.hub.sensors.current_peak.entity:
                self.hub.sensors.current_peak.value = value
            case self.hub.sensors.totalhourlyenergy.entity:
                await self.async_update_total_energy_and_peak(value)
            case self.hub.nordpool.nordpool_entity:
                if self.hub.options.price.price_aware:
                    await self.hub.nordpool.async_update_nordpool()
        return False

    async def _handle_outlet_updates(self):
        if self.hub.chargertype.domainname is ChargerType.Outlet:
            old_state = await self.hub.async_request_sensor_data("chargerobject_value")
            if not self.latest_outlet_update.is_timeout():
                return
            self.latest_outlet_update.update()
            if self.hub.sensors.carpowersensor.value > 0:
                await self.hub.async_set_chargerobject_value("charging")
            else:
                await self.hub.async_set_chargerobject_value("connected")
            if old_state != await self.hub.async_request_sensor_data(
                "chargerobject_value"
            ):
                _LOGGER.debug(
                    f"smartoutlet is now {await self.hub.async_request_sensor_data('chargerobject_value')}"
                )


class StateChangesNoCharger(IStateChanges):
    def __init__(self, hub):
        self.hub = hub
        super().__init__(hub)

    async def async_update_sensor(self, entity, value) -> bool:
        update_session = False
        match entity:
            case self.hub.options.powersensor:
                await self.hub.sensors.power.async_update(
                    carpowersensor_value=0, config_sensor_value=value
                )
                update_session = True
                self.hub.power.power_canary.total_power = (
                    self.hub.sensors.power.total.value
                )
            case self.hub.sensors.totalhourlyenergy.entity:
                await self.async_update_total_energy_and_peak(value)
            case self.hub.sensors.powersensormovingaverage.entity:
                _LOGGER.debug(f"trying to update powersensormovingaverage with {value}")
                self.hub.sensors.powersensormovingaverage.value = value
            case self.hub.sensors.powersensormovingaverage24.entity:
                self.hub.sensors.powersensormovingaverage24.value = value
            case self.hub.nordpool.nordpool_entity:
                if self.hub.options.price.price_aware:
                    await self.hub.nordpool.async_update_nordpool()
                    update_session = True
        return update_session


class StateChangesLiteNoCharger(IStateChanges):
    def __init__(self, hub):
        self.hub = hub
        super().__init__(hub)

    async def async_update_sensor(self, entity, value) -> bool:
        match entity:
            case self.hub.sensors.totalhourlyenergy.entity:
                await self.async_update_total_energy_and_peak(value)
            case self.hub.nordpool.nordpool_entity:
                if self.hub.options.price.price_aware:
                    await self.hub.nordpool.async_update_nordpool()
        return False
