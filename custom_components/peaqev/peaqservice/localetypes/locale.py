from peaqevcore.Locale import LOCALETYPEDICT

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.util.constants import NAME
from custom_components.peaqev.peaqservice.util.sqlsensorhelper import SQLSensorHelper


class LocaleData:
    def __init__(self, input_type, domain):
        self._data = None
        self._type = input_type
        self._domain = domain

        self._data = LOCALETYPEDICT[input_type]

    @property
    def type(self) -> str:
        return self._type

    @property
    def data(self):
        return self._data

    @property
    def current_peak_entity(self) -> str:
        return f"sensor.{self._domain}_{ex.nametoid(SQLSensorHelper('').getquerytype(self.data.observed_peak)[NAME])}"
