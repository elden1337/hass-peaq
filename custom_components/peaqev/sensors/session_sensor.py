import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import ENERGY_KILO_WATT_HOUR
from homeassistant.helpers.restore_state import RestoreEntity

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import SESSION

_LOGGER = logging.getLogger(__name__)


class SessionDevice(SensorEntity):
    should_poll = True

    def __init__(self, hub, name: str, entry_id):
        self.hub = hub
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_available = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.hub.hub_id, SESSION)},
            "name": f"{DOMAIN} {SESSION}",
            "sw_version": 1,
            "manufacturer": "Peaq systems",
        }

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"


class PeaqSessionSensor(SessionDevice, RestoreEntity):
    device_class = SensorDeviceClass.ENERGY
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
        attr_dict["average_session"] = self._average_session
        attr_dict["average_weekly"] = self._average_weekly
        return attr_dict

    async def async_update(self) -> None:
        self._state = getattr(
            self.hub.chargecontroller.charger.session, "session_energy"
        )
        self._average_session = getattr(
            self.hub.chargecontroller.charger.session, "energy_average"
        )
        self._average_weekly = getattr(
            self.hub.chargecontroller.charger.session.core.average_data, "export"
        )

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            _LOGGER.debug("last state of %s = %s", self._attr_name, state)
            self._state = state.state
            self.hub.chargecontroller.charger.session.core.average_data.unpack(
                state.attributes.get("average_weekly", 50)
            )
        else:
            self.hub.chargecontroller.charger.session.core.average_data.set_init_model()


class PeaqSessionCostSensor(SessionDevice, RestoreEntity):
    device_class = SensorDeviceClass.MONETARY

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} Session energy cost"
        super().__init__(hub, name, entry_id)
        self._attr_name = name
        self._attr_unit_of_measurement = None
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

    async def async_update(self) -> None:
        self._state = getattr(
            self.hub.chargecontroller.charger.session, "session_price"
        )
        self._attr_unit_of_measurement = getattr(self.hub.nordpool, "currency")

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            self._state = state.state
        else:
            self._state = 0
