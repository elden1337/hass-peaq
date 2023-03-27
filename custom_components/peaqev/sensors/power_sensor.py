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
        self.hub = hub
        self._state = None
        self._attr_icon = "mdi:current-ac"
        self._charger_current = 0
        self._charger_phases = None
        self._all_currents = None

    @property
    def state(self) -> int:
        return self._state

    async def async_update(self) -> None:
        if self.hub.is_initialized:
            self._state = getattr(self.hub.threshold, "allowedcurrent")
            self._charger_current = self.hub.sensors.chargerobject_switch.current if hasattr(self.hub.sensors, "chargerobject_switch") else 0  #todo: composition
            self._charger_phases = self.hub.threshold.phases  #todo: composition
            self._all_currents = list(self.hub.threshold.currents.values())  #todo: composition

    @property
    def extra_state_attributes(self) -> dict:
        curr = self._charger_current if self._charger_current > 0 else "unreachable"
        return {
            "charger_reported_current": curr,
            "peaqev phase-setting": self._charger_phases,
            "allowed current-list": self._all_currents
        }


class PeaqPowerCostSensor(PowerDevice):
    device_class = SensorDeviceClass.POWER
    unit_of_measurement = POWER_WATT

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} wattage_cost"
        super().__init__(hub, name, entry_id)
        self.hub = hub
        self._state = None
        self._attr_icon = "mdi:cash"

    @property
    def state(self) -> int:
        return self._state

    async def update(self) -> None:
        if self.hub.is_initialized:
            self._state = getattr(self.hub, "watt_cost")

    @property
    def entity_registry_visible_default(self) -> bool:
        return False

 

class PeaqPowerSensor(PowerDevice):
    device_class = SensorDeviceClass.POWER
    unit_of_measurement = POWER_WATT

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {hub.sensors.power.total.name}"  #todo: composition
        super().__init__(hub, name, entry_id)
        self.hub = hub
        self._state = None
        self._attr_icon = "mdi:flash"

    @property
    def state(self) -> int:
        return self._state

    async def async_update(self) -> None:
        if self.hub.is_initialized:
            self._state = getattr(self.hub.sensors.power.total,"value")


class PeaqHousePowerSensor(PowerDevice):
    device_class = SensorDeviceClass.POWER
    unit_of_measurement = POWER_WATT

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {hub.sensors.power.house.name}"  #todo: composition
        super().__init__(hub, name, entry_id)
        self.hub = hub
        self._state = None
        self._attr_icon = "mdi:home-lightning-bolt"

    @property
    def state(self) -> int:
        return self._state


    async def async_update(self) -> None:
        if self.hub.is_initialized:
            self._state = getattr(self.hub.sensors.power.house,"value")
