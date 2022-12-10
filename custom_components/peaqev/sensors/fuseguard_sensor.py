import logging

from custom_components.peaqev.peaqservice.util.constants import FUSEGUARD
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)


class FuseGuardSensor(SensorBase):
    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {FUSEGUARD}"
        super().__init__(hub, name, entry_id)
        self._hub = hub
        self._state = self._hub.fuse_guard.state_string
        self._attr_icon = "mdi:fuse-alert"
        #self._charger_current = self._hub.sensors.chargerobject_switch.current
        #self._charger_phases = self._hub.threshold.phases

    @property
    def state(self) -> int:
        return self._state

    def update(self) -> None:
        self._state = self._hub.fuse_guard.state_string

        #self._charger_current = self._hub.sensors.chargerobject_switch.current
        #self._charger_phases = self._hub.threshold.phases

    # @property
    # def extra_state_attributes(self) -> dict:
    #     curr = self._charger_current if self._charger_current > 0 else "unreachable"
    #     return {
    #         "charger_reported_current": curr,
    #         "peaqev phase-setting": self._charger_phases
    #     }



