import logging
from datetime import datetime

from custom_components.peaqev.peaqservice.util.constants import HOURCONTROLLER
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)

class PeaqMoneySensor(SensorBase):
    """Special sensor which is only created if priceaware is true"""
    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {HOURCONTROLLER}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._nonhours = None
        self._dynamic_caution_hours = None
        self._current_hour = None
        self._currency = None
        self._prices = []
        self._prices_tomorrow = []
        self._current_peak = None

    @property
    def state(self):
        return self._get_written_state()

    @property
    def icon(self) -> str:
        return "mdi:car-clock"

    def update(self) -> None:
        self._nonhours = self._hub.hours.non_hours
        self._dynamic_caution_hours = self._hub.hours.dynamic_caution_hours
        self._currency = self._hub.hours.currency
        self._prices = self._hub.hours.prices if self._hub.hours.prices is not None else []
        self._prices_tomorrow = self._hub.hours.prices_tomorrow if self._hub.hours.prices_tomorrow is not None else []
        self._current_peak = self._hub.currentpeak.value

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {
            "Non hours": self.set_non_hours_display_model(self._nonhours),
            "Caution hours": self.set_dynamic_caution_hours_display(),
            "Current hour charge permittance": self.set_dynamic_caution_hour_display(),
            "Avg price per kWh next 24h": f"{self._hub.hours.get_average_kwh_price()} {self._currency}",
            "Max charge next 24h": f"{self._hub.hours.get_total_charge()} kWh"
        }

        return attr_dict

    def _get_written_state(self) -> str:
        hour = datetime.now().hour
        ret = ""
        if self._hub.timer.is_override:
            return self._hub.timer.override_string
        if hour in self._nonhours:
            for idx, h in enumerate(self._nonhours):
                if idx + 1 < len(self._nonhours):
                    if self._getuneven(self._nonhours[idx + 1], self._nonhours[idx]):
                        ret = self._get_stopped_string(h)
                        break
                elif idx + 1 == len(self._nonhours):
                    ret = self._get_stopped_string(h)
                    break
        elif hour in self._dynamic_caution_hours.keys():
            val = self._dynamic_caution_hours[hour]
            ret = f"Charging allowed at {int(val * 100)}% of peak"
        else:
            ret = "Charging allowed"
        #_LOGGER.debug(f"nonhours: {self._nonhours}, ret:{ret}")
        return ret

    def _get_stopped_string(self, h) -> str:
        val = h + 1 if h + 1 < 24 else h + 1 - 24
        if len(str(val)) == 1:
            return f"Charging stopped until 0{val}:00"
        return f"Charging stopped until {val}:00"

    def _getuneven(self, first, second) -> bool:
        if second > first:
            return first - (second - 24) != 1
        return first - second != 1

    def set_non_hours_display_model(self, input_hour) -> list:
        ret = []
        for i in input_hour:
            if i < datetime.now().hour:
                ret.append(f"{str(i)}⁺¹")
            else:
                ret.append(str(i))
        return ret

    def set_dynamic_caution_hours_display(self) -> dict:
        ret = {}
        if len(self._dynamic_caution_hours) > 0:
            for h in self._dynamic_caution_hours:
                if h < datetime.now().hour:
                    hh = f"{h}⁺¹"
                else:
                    hh = h
                ret[hh] = f"{str((int(self._dynamic_caution_hours[h] * 100)))}%"
        return ret

    def set_dynamic_caution_hour_display(self) -> str:
        hour = datetime.now().hour
        if hour in self._nonhours:
            return "0%"
        if len(self._dynamic_caution_hours) > 0:
            if hour in self._dynamic_caution_hours.keys():
                ret = int(self._dynamic_caution_hours[hour] * 100)
                return f"{str(ret)}%"
        return "100%"
