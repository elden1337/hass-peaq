from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER
from custom_components.peaqev.sensors.sensorbase import SensorBase


class PeaqSensor(SensorBase):
    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {CHARGERCONTROLLER}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = self._hub.chargecontroller.status
        self._nonhours = self._hub.non_hours
        self._cautionhours = self._hub.hours.caution_hours
        self._current_hour = None
        self._price_aware = False

    @property
    def state(self):
        if self._hub.scheduler.scheduler_active:
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
        self._state = self._hub.chargecontroller.status
        self._nonhours = self._hub.non_hours
        self._cautionhours = self._hub.hours.caution_hours
        self._current_hour = self._hub.hours.state
        self._price_aware = self._hub.hours.price_aware

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {}
        attr_dict["price aware"] = self._price_aware
        if self._hub.hours.price_aware is False:
            attr_dict["non_hours"] = self._nonhours
            attr_dict["caution_hours"] = self._cautionhours

        attr_dict["current_hour state"]= self._current_hour
        attr_dict["scheduler_active"] = self._hub.scheduler.scheduler_active
        return attr_dict
