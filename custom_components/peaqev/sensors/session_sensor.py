import logging

from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    ENERGY_KILO_WATT_HOUR,
    DEVICE_CLASS_MONETARY
)
from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)

class PeaqSessionSensor(SensorBase, RestoreEntity):
    device_class = DEVICE_CLASS_ENERGY
    unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} Session energy"
        super().__init__(hub, name, entry_id)
        self._attr_name = name
        self._state = 0
        self._average_session = 0
        self._average_weekly = {}

    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:ev-station"

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {}
        attr_dict["average session"] = self._average_session
        attr_dict["average weekly"] = self._average_weekly
        return attr_dict

    def update(self) -> None:
        self._state = self._hub.charger.session.session_energy
        self._average_session = self._hub.charger.session.energy_average
        self._average_weekly = self._hub.charger.session.energy_weekly_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            self._state = state.state
            self._average_session = state.attributes.get('average session', 50)
            self._average_weekly = state.attributes.get('average weekly', 50)
            if self._average_weekly is None:
                self._average_weekly = {}
            self._hub.charger.session.core.average_data.unpack(self._average_weekly)
            _LOGGER.debug(f"this is average_weekly: {self._hub.charger.session.core.average_data.export}")
        else:
            self._state = 0
            self._average_session = 0
            self._average_weekly = self._hub.charger.session.core.average_data.set_init_model()


class PeaqSessionCostSensor(SensorBase, RestoreEntity):
    device_class = DEVICE_CLASS_MONETARY

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} Session energy cost"
        super().__init__(hub, name, entry_id)
        self._attr_name = name
        self._attr_unit_of_measurement = self._hub.nordpool.currency
        self._state = 0

    @property
    def state(self) -> float:
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:cash-multiple"

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

    def update(self) -> None:
        self._state = self._hub.charger.session.session_price
        self._attr_unit_of_measurement = self._hub.nordpool.currency

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            self._state = state.state
        else:
            self._state = 0
