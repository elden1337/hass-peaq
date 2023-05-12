from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
import logging

from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.util.constants import \
    CHARGERCONTROLLER
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)


class PeaqSensor(SensorBase):
    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f"{hub.hubname} {CHARGERCONTROLLER}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None
        self._nonhours = None
        self._cautionhours = None
        self._current_hour = None
        self._price_aware: bool = False
        self._scheduler_active: bool = False

    @property
    def state(self):
        if self._scheduler_active:
            return f"(schedule) {self._state}"
        return self._state

    @property
    def icon(self) -> str:
        ret = "mdi:battery"
        if self.state is ChargeControllerStates.Idle.value:
            ret = "mdi:ev-plug-type2"
        elif self.state is ChargeControllerStates.Connected.value:
            ret = "mdi:car-connected"
        elif self.state is ChargeControllerStates.Start.value:
            ret = "mdi:battery-charging"
        elif self.state is ChargeControllerStates.Stop.value:
            ret = "mdi:battery-clock"
        elif self.state is ChargeControllerStates.Done.value:
            ret = "mdi:battery-charging-100"
        return ret

    async def async_update(self) -> None:
        ret = await self.hub.async_request_sensor_data(
            "non_hours",
            "caution_hours",
            "chargecontroller_status",
            "hour_state",
            "is_price_aware",
            "is_scheduler_active",
        )
        if ret is not None:
            self._state = ret.get("chargecontroller_status")
            self._nonhours = ret.get("non_hours")
            self._cautionhours = ret.get("caution_hours")
            self._current_hour = ret.get("hour_state")
            self._price_aware = ret.get("is_price_aware")
            self._scheduler_active = ret.get("is_scheduler_active")

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {}
        attr_dict["price aware"] = self._price_aware
        if self.hub.hours.price_aware is False:
            attr_dict["non_hours"] = self._nonhours
            attr_dict["caution_hours"] = self._cautionhours

        attr_dict["current_hour state"] = self._current_hour
        attr_dict["scheduler_active"] = self._scheduler_active
        return attr_dict
