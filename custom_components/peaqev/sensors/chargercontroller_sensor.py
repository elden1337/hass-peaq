from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.peaqev.peaqservice.hub.const import LookupKeys

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
import logging

from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.util.constants import \
    CHARGERCONTROLLER
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)


class ChargerControllerSensor(SensorBase):
    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f'{hub.hubname} {CHARGERCONTROLLER}'
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None
        self._nonhours: list = []
        self._cautionhours = None
        self._current_hour = None
        self._price_aware: bool = False
        self._scheduler_active: bool = False
        self._schedules = None

    @property
    def state(self):
        if self._scheduler_active:
            return f'(schedule) {self._state}'
        return self._state

    @property
    def icon(self) -> str:
        ret = 'mdi:battery'
        if self.state is ChargeControllerStates.Idle.value:
            ret = 'mdi:ev-plug-type2'
        elif self.state is ChargeControllerStates.Connected.value:
            ret = 'mdi:car-connected'
        elif self.state is ChargeControllerStates.Start.value:
            ret = 'mdi:battery-charging'
        elif self.state is ChargeControllerStates.Stop.value:
            ret = 'mdi:battery-clock'
        elif self.state is ChargeControllerStates.Done.value:
            ret = 'mdi:battery-charging-100'
        return ret

    async def async_update(self) -> None:
        ret = await self.hub.async_request_sensor_data(
            LookupKeys.NON_HOURS,
            LookupKeys.CAUTION_HOURS,
            LookupKeys.CHARGECONTROLLER_STATUS,
            LookupKeys.HOUR_STATE,
            LookupKeys.IS_PRICE_AWARE,
            LookupKeys.IS_SCHEDULER_ACTIVE,
            LookupKeys.SCHEDULES
        )
        if ret is not None:
            self._state = ret.get(LookupKeys.CHARGECONTROLLER_STATUS)
            self._nonhours = ret.get(LookupKeys.NON_HOURS)
            self._cautionhours = ret.get(LookupKeys.CAUTION_HOURS)
            self._current_hour = ret.get(LookupKeys.HOUR_STATE)
            self._price_aware = ret.get(LookupKeys.IS_PRICE_AWARE)
            self._scheduler_active = ret.get(LookupKeys.IS_SCHEDULER_ACTIVE)
            self._schedules = ret.get(LookupKeys.SCHEDULES)

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {}
        attr_dict['price aware'] = self._price_aware
        if self.hub.hours.price_aware is False:
            attr_dict['non_hours'] = self._nonhours
            attr_dict['caution_hours'] = self._cautionhours
        else:
            attr_dict['non_hours'] = self.hub.options.nonhours
        attr_dict['current_hour state'] = self._current_hour
        attr_dict['scheduler_active'] = self._scheduler_active
        attr_dict['schedules'] = self._schedules
        return attr_dict
