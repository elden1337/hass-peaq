from custom_components.peaqev.sensors.sensorbase import SensorBase
from custom_components.peaqev.peaqservice.util.constants import MONEY
from datetime import datetime


class PeaqMoneySensor(SensorBase):
    """Special sensor which is only created if priceaware is true"""
    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {MONEY}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._nonhours = None
        self._dynamic_caution_hours = None
        self._current_hour = None,
        self._price_aware = False,
        self._absolute_top_price = None
        self._currency = None
        self._cautionhour_type_string = None

    @property
    def state(self):
        return self.get_written_state()

    @property
    def icon(self) -> str:
        return "mdi:car-clock"

    def update(self) -> None:
        self._nonhours = self._hub.hours.non_hours
        self._dynamic_caution_hours = self._hub.hours.dynamic_caution_hours
        self._current_hour = self._hub.hours.state
        self._price_aware = self._hub.hours.price_aware
        self._absolute_top_price = self._hub.hours.absolute_top_price if 0 < self._hub.hours.absolute_top_price < float("inf") else "-"
        self._currency = self._hub.hours.currency
        self._cautionhour_type_string = self._hub.hours.cautionhour_type_string

    @property
    def extra_state_attributes(self) -> dict:
        dict = {
            "Non hours": self._nonhours,
            "Caution hours": self.set_dynamic_caution_hours_display(),
            "Current hour state": self._current_hour,
            "Absolute top price": f"{self._absolute_top_price} {self._currency}",
            "Caution hour type": self._cautionhour_type_string,
            "Current hour charge permittance": self.set_dynamic_caution_hour_display()
        }
        return dict

    def get_written_state(self) -> str:
        hour = datetime.now().hour
        ret = ""
        if hour in self._nonhours:
            for idx, h in enumerate(self._nonhours):
                if idx + 1 < len(self._nonhours):
                    if self.getuneven(self._nonhours[idx + 1], self._nonhours[idx]):
                        val = h + 1 if h + 1 < 24 else h + 1 - 24
                        if len(str(val)) == 1:
                            ret = f"Charging stopped until 0{val}:00"
                        else:
                            ret = f"Charging stopped until {val}:00"
                        break
        elif hour in self._dynamic_caution_hours.keys():
            val = self._dynamic_caution_hours[hour]
            ret = f"Charging allowed at {int(val * 100)}% of peak"
        else:
            ret = "Charging allowed"
        return ret

    def getuneven(self, first, second) -> bool:
        if second > first:
            return first - (second - 24) != 1
        return first - second != 1

    def set_dynamic_caution_hours_display(self) -> dict:
        ret = {}
        if len(self._dynamic_caution_hours) > 0:
            for h in self._dynamic_caution_hours:
                hh = int(h)
                ret[hh] = f"{str((int(self._dynamic_caution_hours[h] * 100)))}%"
        return ret

    def set_dynamic_caution_hour_display(self) -> str:
        if datetime.now().hour in self._nonhours:
            return "0%"
        if len(self._dynamic_caution_hours) > 0:
            if datetime.now().hour in  self._dynamic_caution_hours.keys():
                ret = int(self._dynamic_caution_hours[datetime.now().hour] * 100)
                return f"{str(ret)}%"
        return "100%"