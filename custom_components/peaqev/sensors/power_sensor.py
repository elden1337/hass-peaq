from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    POWER_WATT,
    ELECTRIC_CURRENT_AMPERE
)

from custom_components.peaqev.peaqservice.util.constants import ALLOWEDCURRENT
from custom_components.peaqev.sensors.sensorbase import SensorBase


class PeaqAmpSensor(SensorBase):
    device_class = SensorDeviceClass.CURRENT
    unit_of_measurement = ELECTRIC_CURRENT_AMPERE
    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {ALLOWEDCURRENT}"
        super().__init__(hub, name, entry_id)
        self._hub = hub
        self._state = self._hub.threshold.allowedcurrent
        self._attr_icon = "mdi:current-ac"
        self._charger_current = self._hub.chargerobject_switch.current

    @property
    def state(self) -> int:
        return self._state

    def update(self) -> None:
        self._state = self._hub.threshold.allowedcurrent
        self._charger_current = self._hub.chargerobject_switch.current

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "charger_reported_current": self._charger_current,
        }

class PeaqPowerSensor(SensorBase):
    device_class = SensorDeviceClass.POWER
    unit_of_measurement = POWER_WATT

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {hub.power.total.name}"
        super().__init__(hub, name, entry_id)
        self._hub = hub
        self._state = self._hub.power.total.value
        self._attr_icon = "mdi:flash"

    @property
    def state(self) -> int:
        return self._state

    def update(self) -> None:
        self._state = self._hub.power.total.value

class PeaqHousePowerSensor(SensorBase):
    device_class = SensorDeviceClass.POWER
    unit_of_measurement = POWER_WATT

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {hub.power.house.name}"
        super().__init__(hub, name, entry_id)
        self._hub = hub
        self._state = self._hub.power.house.value
        self._attr_icon = "mdi:home-lightning-bolt"

    @property
    def state(self) -> int:
        return self._state

    def update(self) -> None:
        self._state = self._hub.power.house.value
