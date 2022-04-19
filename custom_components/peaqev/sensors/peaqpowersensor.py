from custom_components.peaqev.sensors.sensorbase import SensorBase
from custom_components.peaqev.peaqservice.util.constants import ALLOWEDCURRENT

from homeassistant.const import (
    DEVICE_CLASS_POWER,
    POWER_WATT,
    DEVICE_CLASS_CURRENT,
    ELECTRIC_CURRENT_AMPERE
)

class PeaqAmpSensor(SensorBase):
    device_class = DEVICE_CLASS_CURRENT
    unit_of_measurement = ELECTRIC_CURRENT_AMPERE
    
    def __init__(self, hub, hass):
        name = f"{hub.hubname} {ALLOWEDCURRENT}"
        super().__init__(hub, name)
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
    device_class = DEVICE_CLASS_POWER
    unit_of_measurement = POWER_WATT
    
    def __init__(self, hub, hass):
        name = f"{hub.hubname} {hub.totalpowersensor.name}"
        super().__init__(hub, name)
        self._hub = hub
        self._state = self._hub.totalpowersensor.value
        self._attr_icon = "mdi:flash"

    @property
    def state(self) -> int:
        return self._state

    def update(self) -> None:
        self._state = self._hub.totalpowersensor.value