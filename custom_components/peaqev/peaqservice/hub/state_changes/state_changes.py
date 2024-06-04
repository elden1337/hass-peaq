from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.chargertypes.types.outlet import (
    OUTLET_TYPE_CHARGING, OUTLET_TYPE_CONNECTED)
from custom_components.peaqev.peaqservice.hub.const import LookupKeys
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import \
    StateChangesBase

_LOGGER = logging.getLogger(__name__)


class StateChanges(StateChangesBase):
    def __init__(self, hub: HomeAssistantHub, chargertype: ChargerType):
        super().__init__(hub, chargertype)

    async def async_update_sensor_internal(self, entity, value) -> bool:
        try:
            update_session = False
            match entity:
                case self.hub.options.powersensor:
                    await self.async_handle_powersensor(value)
                    update_session = True
                case self.hub.sensors.carpowersensor.entity:
                    await self.async_handle_carpowersensor(value)
                    await self.async_handle_outlet_updates()
                    update_session = True
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
                case self.hub.spotprice.entity:
                    await self.hub.async_update_spotprice()
                    update_session = True
            return update_session
        except Exception as e:
            _LOGGER.error(f'async_update_sensor_internal for {entity}: {e}')
            return False

    async def async_handle_powersensor(self, value) -> None:
        await self.hub.sensors.power.async_update(
            carpowersensor_value=self.hub.sensors.carpowersensor.value,
            config_sensor_value=value,
        )
        self.hub.power.power_canary.total_power = (
            self.hub.sensors.power.total.value
        )
        self.hub.sensors.power_trend.add_reading(self.hub.sensors.power.total.value, time.time())

    async def async_handle_carpowersensor(self, value) -> None:
        if self.hub.sensors.carpowersensor.use_attribute:
            return
        else:
            self.hub.sensors.carpowersensor.value = value
            await self.hub.sensors.power.async_update(
                carpowersensor_value=self.hub.sensors.carpowersensor.value,
                config_sensor_value=None,
            )
        self.hub.power.power_canary.total_power = (
            self.hub.sensors.power.total.value
        )
    async def async_handle_outlet_updates(self):
        if self.chargertype is ChargerType.Outlet:
            old_state = await self.hub.async_request_sensor_data(LookupKeys.CHARGEROBJECT_VALUE)
            if not self.latest_outlet_update.is_timeout():
                return
            self.latest_outlet_update.update()
            if self.hub.sensors.carpowersensor.value > 0:
                await self.hub.async_set_chargerobject_value(OUTLET_TYPE_CHARGING)
            else:
                await self.hub.async_set_chargerobject_value(OUTLET_TYPE_CONNECTED)
            if old_state != await self.hub.async_request_sensor_data(LookupKeys.CHARGEROBJECT_VALUE):
                _LOGGER.debug(
                    f'smartoutlet is now {await self.hub.async_request_sensor_data(LookupKeys.CHARGEROBJECT_VALUE)}'
                )


class StateChangesLite(StateChangesBase):
    def __init__(self, hub, chargertype: ChargerType):
        super().__init__(hub, chargertype)

    async def async_update_sensor_internal(self, entity, value) -> bool:
        match entity:
            case self.hub.sensors.carpowersensor.entity:
                if self.hub.sensors.carpowersensor.use_attribute:
                    pass
                else:
                    self.hub.sensors.carpowersensor.value = value
                    await self._handle_outlet_updates()
            case self.hub.sensors.chargerobject.entity:
                await self.hub.async_set_chargerobject_value(value)
            case self.hub.sensors.chargerobject_switch.entity:
                await self.async_update_chargerobject_switch(value)
            case self.hub.sensors.totalhourlyenergy.entity:
                await self.async_update_total_energy_and_peak(value)
            case self.hub.spotprice.entity:
                await self.hub.async_update_spotprice()
        return False

    async def _handle_outlet_updates(self):
        if self.chargertype is ChargerType.Outlet:
            old_state = await self.hub.async_request_sensor_data(LookupKeys.CHARGEROBJECT_VALUE)
            if not self.latest_outlet_update.is_timeout():
                return
            self.latest_outlet_update.update()
            if self.hub.sensors.carpowersensor.value > 0:
                await self.hub.async_set_chargerobject_value(OUTLET_TYPE_CHARGING)
            else:
                await self.hub.async_set_chargerobject_value(OUTLET_TYPE_CONNECTED)
            if old_state != await self.hub.async_request_sensor_data(LookupKeys.CHARGEROBJECT_VALUE):
                _LOGGER.debug(
                    f'smartoutlet is now {await self.hub.async_request_sensor_data(LookupKeys.CHARGEROBJECT_VALUE)}'
                )


class StateChangesNoCharger(StateChangesBase):
    def __init__(self, hub, chargertype: ChargerType):
        super().__init__(hub, chargertype)

    async def async_update_sensor_internal(self, entity, value) -> bool:
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
                self.hub.sensors.power_trend.add_reading(self.hub.sensors.power.total.value, time.time())
                self.hub.sensors.power_sensor_moving_average_5.add_reading(self.hub.sensors.power.total.value)
            case self.hub.sensors.totalhourlyenergy.entity:
                await self.async_update_total_energy_and_peak(value)
            case self.hub.sensors.powersensormovingaverage.entity:
                _LOGGER.debug(f'trying to update powersensormovingaverage with {value}')
                self.hub.sensors.powersensormovingaverage.value = value
            case self.hub.sensors.powersensormovingaverage24.entity:
                self.hub.sensors.powersensormovingaverage24.value = value
            case self.hub.spotprice.entity:
                await self.hub.async_update_spotprice()
                update_session = True
        return update_session


class StateChangesLiteNoCharger(StateChangesBase):
    def __init__(self, hub, chargertype: ChargerType):
        super().__init__(hub, chargertype)

    async def async_update_sensor_internal(self, entity, value) -> bool:
        match entity:
            case self.hub.sensors.totalhourlyenergy.entity:
                await self.async_update_total_energy_and_peak(value)
            case self.hub.spotprice.entity:
                await self.hub.async_update_spotprice()
        return False
