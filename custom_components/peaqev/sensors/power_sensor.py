import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    POWER_WATT,
    ELECTRIC_CURRENT_AMPERE
)

from custom_components.peaqev.peaqservice.util.constants import ALLOWEDCURRENT
from custom_components.peaqev.sensors.sensorbase import PowerDevice

_LOGGER = logging.getLogger(__name__)


class PeaqAmpSensor(PowerDevice):
    device_class = SensorDeviceClass.ENERGY
    unit_of_measurement = ELECTRIC_CURRENT_AMPERE

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {ALLOWEDCURRENT}"
        super().__init__(hub, name, entry_id)
        self._hub = hub
        self._state = self._hub.threshold.allowedcurrent
        self._attr_icon = "mdi:current-ac"
        self._charger_current = self._hub.sensors.chargerobject_switch.current
        self._charger_phases = self._hub.threshold.phases

    @property
    def state(self) -> int:
        return self._state

    def update(self) -> None:
        self._state = self._hub.threshold.allowedcurrent
        self._charger_current = self._hub.sensors.chargerobject_switch.current
        self._charger_phases = self._hub.threshold.phases

    @property
    def extra_state_attributes(self) -> dict:
        curr = self._charger_current if self._charger_current > 0 else "unreachable"
        return {
            "charger_reported_current": curr,
            "peaqev phase-setting": self._charger_phases
        }


class PeaqPowerSensor(PowerDevice):
    device_class = SensorDeviceClass.POWER
    unit_of_measurement = POWER_WATT

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {hub.sensors.power.total.name}"
        super().__init__(hub, name, entry_id)
        self._hub = hub
        self._state = self._hub.sensors.power.total.value
        self._attr_icon = "mdi:flash"

    @property
    def state(self) -> int:
        return self._state

    def update(self) -> None:
        self._state = self._hub.sensors.power.total.value


class PeaqHousePowerSensor(PowerDevice):
    device_class = SensorDeviceClass.POWER
    unit_of_measurement = POWER_WATT

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {hub.sensors.power.house.name}"
        super().__init__(hub, name, entry_id)
        self._hub = hub
        self._state = self._hub.sensors.power.house.value
        self._attr_icon = "mdi:home-lightning-bolt"

    @property
    def state(self) -> int:
        return self._state

    def update(self) -> None:
        self._state = self._hub.sensors.power.house.value
