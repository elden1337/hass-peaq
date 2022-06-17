import logging
from datetime import datetime

import custom_components.peaqev.peaqservice.util.extensionmethods as ex

_LOGGER = logging.getLogger(__name__)


class HubMember:
    def __init__(self, data_type, listenerentity = None, initval = None, name = None):
        self._value = initval
        self._type = data_type
        self._listenerentity = listenerentity
        self.name = name
        self.id = ex.nametoid(self.name) if self.name is not None else None
        self.warned_not_initialized = False
        self._is_initialized = False

    @property
    def is_initialized(self) -> bool:
        if self._is_initialized:
            return True
        if isinstance(self.value, self._type):
            _LOGGER.debug(f"{self._listenerentity} has initialized")
            self._is_initialized = True
            return True
        if not self.warned_not_initialized:
            _LOGGER.error(f"{self._listenerentity} was not {self._type}. {self.value}")
            self.warned_not_initialized = True
        return False

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
        if isinstance(value, self._type):
            self._value = value
        elif self._type is float:
            try:
                self._value = float(value)
            except ValueError:
                self._value = 0
        elif self._type is int:
            try:
                self._value = int(float(value))
            except ValueError:
                self._value = 0
        elif self._type is bool:
            try:
                if value is None:
                    self._value = False
                elif value.lower() == "on":
                    self._value = True
                elif value.lower() == "off":
                    self._value = False
            except ValueError as e:
                msg = f"Could not parse bool, setting to false to be sure {value}, {self._listenerentity}, {e}"
                _LOGGER.error(msg)
                self._value = False
        elif  self._type is str:
            self._value = str(value)


class CurrentPeak(HubMember):
    NAME = "CurrentPeak-sensor"

    def __init__(self, data_type: type, initval, startpeaks:dict):
        self._startpeak = self._set_start_peak(startpeaks)
        self._value = initval
        super().__init__(data_type, initval)

    def _set_start_peak(self, peaks:dict) -> float:
        peak = peaks.get(datetime.now().month)
        if peak is None:
            peak = peaks.get(str(datetime.now().month))
            if peak is None:
                raise ValueError
        return peak

    @HubMember.value.getter
    def value(self): # pylint:disable=invalid-overridden-method
        return max(self._value, float(self._startpeak)) if self._value is not None else float(self._startpeak)


class CarPowerSensor(HubMember):
    NAME = "CarPower-sensor"

    def __init__(
            self,
            data_type: type,
            listenerentity=None,
            initval=None,
            powermeter_factor=1,
            hubdata=None
    ):
        self._hubdata = hubdata
        self._powermeter_factor = powermeter_factor
        self._warned_not_initialized = False
        self._is_initialized = False
        super().__init__(data_type, listenerentity, initval)

    @property
    def is_initialized(self) -> bool:
        if self._is_initialized is True:
            return True
        if isinstance(self.value, (float,int)) and self._hubdata.chargerobject.is_initialized:
            _LOGGER.debug(f"{self.NAME} has initialized")
            self._is_initialized = True
            return True
        return False

    @HubMember.value.setter
    def value(self, val):
        if val is None or val == 0:
            self._value = 0
        vval = ex.try_parse(val, float)
        if not vval:
            vval = ex.try_parse(val, int)
        if not vval:
            self._value = 0
        else:
            self._value = float(vval * self._powermeter_factor)


class ChargerObject(HubMember):
    def __init__(self, data_type:list, listenerentity):
        self._type = data_type
        self._listenerentity = listenerentity
        self._warned_not_initialized = False
        self._is_initialized = False
        super().__init__(data_type, listenerentity)

    @property
    def is_initialized(self) -> bool:
        if self._is_initialized is True:
            return True
        if self.value is not None:
            if str(self.value).lower() in self._type:
               _LOGGER.debug("Chargerobject has initialized")
               self._is_initialized = True
               return True
        if not self._warned_not_initialized:
            _LOGGER.warning(f"Chargerobject-state not found in given state-list. Value was: {self.value}")
            self._warned_not_initialized = True
        return False

    @HubMember.value.setter
    def value(self, value):
        self._value = value
