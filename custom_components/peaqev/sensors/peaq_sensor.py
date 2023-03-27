from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER
from custom_components.peaqev.sensors.sensorbase import SensorBase


class PeaqSensor(SensorBase):
    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {CHARGERCONTROLLER}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None
        self._nonhours = None
        self._cautionhours = None
        self._current_hour = None
        self._price_aware: bool = False
        self._scheduler_active: bool = False
        self._latest_charger_start = None

    @property
    def state(self):
        if self._scheduler_active:
            return f"(schedule) {self._state}"
        return self._state

    @property
    def icon(self) -> str:
        ret = "mdi:electric-switch-closed"
        if self.state == "Idle":
            ret = "mdi:electric-switch"
        elif self.state == "Done":
            ret = "mdi:check"
        return ret

    def update(self) -> None:
        self._state = self.hub.chargecontroller.status_string  #todo: composition
        self._nonhours = self.hub.hours.non_hours  #todo: composition
        self._cautionhours = self.hub.hours.caution_hours  #todo: composition
        self._current_hour = self.hub.hours.state  #todo: composition
        self._price_aware = self.hub.hours.price_aware  #todo: composition
        self._latest_charger_start = self.hub.chargecontroller.latest_charger_start
        self._scheduler_active = self.hub.scheduler.scheduler_active

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {}
        attr_dict["price aware"] = self._price_aware
        if self.hub.hours.price_aware is False:
            attr_dict["non_hours"] = self._nonhours
            attr_dict["caution_hours"] = self._cautionhours

        attr_dict["current_hour state"] = self._current_hour
        attr_dict["scheduler_active"] = self._scheduler_active
        attr_dict["latest_internal_chargerstart"] = self._latest_charger_start
        return attr_dict
