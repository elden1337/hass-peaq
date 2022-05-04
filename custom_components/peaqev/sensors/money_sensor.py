from custom_components.peaqev.sensors.sensorbase import MoneySensor
from custom_components.peaqev.peaqservice.util.constants import MONEY

class PeaqMoneySensor(MoneySensor):
    def __init__(self, hub):
        name = f"{hub.hubname} {MONEY}"
        super().__init__(hub, name)

        self._attr_name = name
        self._state = self._hub.chargecontroller.status.name
        self._nonhours = None
        self._cautionhours = None
        self._current_hour = None,
        self._price_aware = False,
        self._absolute_top_price = None
        self._currency = None
        self._cautionhour_type_string = None

    @property
    def state(self):
        return self._hub.chargecontroller.status.name

    @property
    def icon(self) -> str:
        pass
        # ret = "mdi:electric-switch-closed"
        # if self.state == "Idle":
        #     ret = "mdi:electric-switch"
        # elif self.state == "Done":
        #     ret = "mdi:check"
        # return ret

    def update(self) -> None:
        self._state = self._hub.chargecontroller.status.name
        self._nonhours = self._hub.hours.non_hours
        self._cautionhours = self._hub.hours.caution_hours
        self._current_hour = self._hub.hours.state
        self._price_aware = self._hub.hours.price_aware
        self._absolute_top_price = self._hub.hours.absolute_top_price if self._price_aware is True else "-"
        self._currency = self._hub.hours.currency if self._price_aware is True else ""
        self._cautionhour_type_string = self._hub.hours.cautionhour_type_string if self._price_aware is True else ""

    @property
    def extra_state_attributes(self) -> dict:
        dict = {
            "non_hours": self._nonhours,
            "caution_hours": self._cautionhours,
            "current_hour state": self._current_hour,
            "price aware": self._price_aware,
        }

        if self._price_aware is True:
            dict["absolute top price"] = f"{self._absolute_top_price} {self.currency}"
            dict["cautionhour_type"] = self._cautionhour_type_string

        return dict