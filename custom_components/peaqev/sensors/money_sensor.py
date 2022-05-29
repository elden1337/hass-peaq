from datetime import datetime

from custom_components.peaqev.peaqservice.util.constants import HOURCONTROLLER
from custom_components.peaqev.sensors.sensorbase import SensorBase


class PeaqMoneySensor(SensorBase):
    """Special sensor which is only created if priceaware is true"""
    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {HOURCONTROLLER}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._nonhours = None
        self._dynamic_caution_hours = None
        self._current_hour = None
        self._price_aware = False
        self._absolute_top_price = None
        self._min_price = None
        self._currency = None
        self._cautionhour_type_string = None

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
        self._price_aware = self._hub.hours.price_aware
        self._absolute_top_price = self._hub.hours.absolute_top_price if 0 < self._hub.hours.absolute_top_price < float("inf") else None
        self._min_price = self._hub.hours.min_price if self._hub.hours.min_price is not None and self._hub.hours.min_price > 0 else None
        self._currency = self._hub.hours.currency
        self._cautionhour_type_string = self._hub.hours.cautionhour_type_string
        self._prices = self._hub.hours.prices if self._hub.hours.prices is not None else []
        self._prices_tomorrow = self._hub.hours.prices_tomorrow if self._hub.hours.prices_tomorrow is not None else []
        self._current_peak = self._hub.currentpeak.value

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {
            "Non hours": self.set_non_hours_display_model(self._nonhours),
            "Caution hours": self.set_dynamic_caution_hours_display(),
            "Caution hour type": self._cautionhour_type_string,
            "Current hour charge permittance": self.set_dynamic_caution_hour_display(),
            "Avg price per kWh next 24h": f"{self._get_average_kwh_price()} {self._currency}",
            "Max charge next 24h": f"{self._get_total_charge()} kWh"
        }
        if self._absolute_top_price is not None:
            attr_dict["Absolute top price"] = f"{self._absolute_top_price} {self._currency}"
        if self._min_price is not None:
            attr_dict["Min caution price"]= f"{self._min_price} {self._currency}"

        return attr_dict

    def _get_average_kwh_price(self):
        if len(self._prices) > 0:
            hour = datetime.now().hour
            ret = {}

            for h in self._dynamic_caution_hours:
                if h < hour and len(self._prices_tomorrow) > 0:
                    ret[h] = self._dynamic_caution_hours[h] * self._prices_tomorrow[h]
                elif h >= hour:
                    ret[h] = self._dynamic_caution_hours[h] * self._prices[h]

            for nh in self._nonhours:
                ret[nh] = 0

            for i in range(0,23):
                if i not in ret.keys():
                    if i < hour and len(self._prices_tomorrow) > 0:
                        ret[i] = self._prices_tomorrow[i]
                    elif i >= hour:
                        ret[i] = self._prices[i]

            return round(sum(ret.values())/len(ret),2)
        return "-"

    def _get_total_charge(self) -> float:
        ret = {}

        for h in self._dynamic_caution_hours:
            ret[h] = self._dynamic_caution_hours[h] * self._current_peak
        for h in self._nonhours:
            ret[h] = 0
        for i in range(0,23):
            if i not in ret.keys():
                ret[i] = self._current_peak

        return round(sum(ret.values()),1)

    def _get_written_state(self) -> str:
        hour = datetime.now().hour
        ret = ""
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
