import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.localetypes.types.default import Default
from custom_components.peaqev.peaqservice.localetypes.types.se_gothenburg import SE_Gothenburg
from custom_components.peaqev.peaqservice.localetypes.types.se_karlstad import SE_Karlstad
from custom_components.peaqev.peaqservice.localetypes.types.se_kristinehamn import SE_Kristinehamn
from custom_components.peaqev.peaqservice.localetypes.types.se_malung_salen import SE_Malung_Salen
from custom_components.peaqev.peaqservice.localetypes.types.se_nacka import SE_Nacka_normal
from custom_components.peaqev.peaqservice.localetypes.types.se_partille import SE_Partille
from custom_components.peaqev.peaqservice.localetypes.types.se_she_ab import SE_SHE_AB
from custom_components.peaqev.peaqservice.localetypes.types.se_skovde import SE_Skovde
from custom_components.peaqev.peaqservice.localetypes.types.se_sollentuna import SE_Sollentuna
from custom_components.peaqev.peaqservice.util.constants import (
    LOCALE_DEFAULT,
    LOCALE_SE_GOTHENBURG,
    LOCALE_SE_PARTILLE,
    LOCALE_SE_KARLSTAD,
    LOCALE_SE_KRISTINEHAMN,
    LOCALE_SE_NACKA_NORMAL,
    LOCALE_SE_MALUNG_SALEN,
    LOCALE_SE_SALA,
    LOCALE_SE_SKOVDE,
    LOCALE_SE_SOLLENTUNA,
    NAME
)
from custom_components.peaqev.peaqservice.util.sqlsensorhelper import SQLSensorHelper

LOCALETYPEDICT = {
    LOCALE_DEFAULT: Default(),
    LOCALE_SE_GOTHENBURG: SE_Gothenburg(),
    LOCALE_SE_PARTILLE: SE_Partille(),
    LOCALE_SE_KARLSTAD: SE_Karlstad(),
    LOCALE_SE_KRISTINEHAMN: SE_Kristinehamn(),
    LOCALE_SE_NACKA_NORMAL: SE_Nacka_normal(),
    LOCALE_SE_MALUNG_SALEN: SE_Malung_Salen(),
    LOCALE_SE_SALA: SE_SHE_AB(),
    LOCALE_SE_SKOVDE: SE_Skovde(),
    LOCALE_SE_SOLLENTUNA: SE_Sollentuna()
}

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
