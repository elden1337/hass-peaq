import logging
from datetime import datetime
import custom_components.peaqev.peaqservice.util.extensionmethods as ex

_LOGGER = logging.getLogger(__name__)


class HubMember:
    def __init__(self, type: type, listenerentity = None, initval = None, name = None):
        self._value = initval
        self._type = type
        self._listenerentity = listenerentity
        self.name = name
        self.id = ex.nametoid(self.name) if self.name is not None else None

    @property
    def entity(self) -> str:
        return self._listenerentity

    @entity.setter
    def entity(self, val: str):
        self._listenerentity = val

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if type(value) is self._type:
            self._value = value
        elif self._type is float:
            try:
                self._value = float(value)
            except:
                self._value = 0
        elif self._type is int:
            try:
                self._value = int(float(value))
            except:
                self._value = 0
        elif self._type is bool:
            try:
                if value is None:
                    self._value = False
                elif value.lower() == "on":
                    self._value = True
                elif value.lower() == "off":
                    self._value = False
            except:
                _LOGGER.warn("Could not parse bool, setting to false to be sure", value, self._listenerentity)
                self._value = False
        elif  self._type is str:
            self._value = str(value)


class CurrentPeak(HubMember):
    def __init__(self, type: type, listenerentity, initval, startpeaks:dict):

        self._startpeak = self._set_start_peak(startpeaks)
        self._value = initval
        super().__init__(type, listenerentity, initval)

    def _set_start_peak(self, peaks:dict) -> float:
        peak = peaks.get(datetime.now().month)
        if peak is None:
            peak = peaks.get(str(datetime.now().month))
            if peak is None:
                raise ValueError
        return peak

    @HubMember.value.getter
    def value(self):
        return max(self._value, float(self._startpeak)) if self._value is not None else float(self._startpeak)


class CarPowerSensor(HubMember):
    def __init__(self, type: type, listenerentity=None, initval=None, powermeter_factor=1):
        self._powermeter_factor = powermeter_factor
        super().__init__(type, listenerentity, initval)

    @HubMember.value.setter
    def value(self, val):
        if val is None or val == 0:
            self._value = 0
        elif ex.try_parse(val, float) is True:
            self._value = float(val * self._powermeter_factor)
        elif ex.try_parse(val, int) is True:
            self._value = float(val * self._powermeter_factor)
        else:
            self._value = 0


class ChargerSwitch(HubMember):
    def __init__(self, hass, type: type, listenerentity, initval, currentname: str, ampmeter_is_attribute: bool):
        self._hass = hass
        self._value = initval
        self._current = 0
        self._current_attr_name = currentname
        self._ampmeter_is_attribute = ampmeter_is_attribute
        super().__init__(type, listenerentity, initval)

    @property
    def current(self) -> int:
        if self._current == 0:
            return 6
        return self._current

    @current.setter
    def current(self, value):
        try:
            self._current = int(value)
        except:
            msg = f"[{value}] could not set value as chargercurrent"
            _LOGGER.warn(msg)

    def updatecurrent(self):
        if self._ampmeter_is_attribute is True:
            ret = self._hass.states.get(self.entity)
            if ret is not None:
                ret_attr = str(ret.attributes.get(self._current_attr_name))
                self.current = ret_attr
            else:
                _LOGGER.error("chargerobject state was none")
        else:
            ret = self._hass.states.get(self._current_attr_name)
            if ret is not None:
                self.current = ret.state
            else:
                _LOGGER.error("chargerobject state was none")