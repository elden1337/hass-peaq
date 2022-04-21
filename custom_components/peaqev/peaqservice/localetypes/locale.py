import custom_components.peaqev.peaqservice.util.constants as constants
import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.localetypes.types.default import Default
from custom_components.peaqev.peaqservice.localetypes.types.se_gothenburg import SE_Gothenburg
from custom_components.peaqev.peaqservice.localetypes.types.se_karlstad import SE_Karlstad
from custom_components.peaqev.peaqservice.localetypes.types.se_kristinehamn import SE_Kristinehamn
from custom_components.peaqev.peaqservice.localetypes.types.se_malung_salen import SE_Malung_Salen
from custom_components.peaqev.peaqservice.localetypes.types.se_nacka import SE_Nacka_normal
from custom_components.peaqev.peaqservice.localetypes.types.se_partille import SE_Partille
from custom_components.peaqev.peaqservice.localetypes.types.se_sala import SE_Sala
from custom_components.peaqev.peaqservice.localetypes.types.se_skovde import SE_Skovde
from custom_components.peaqev.sensors.peaqsqlsensor import PeaqSQLSensorHelper

LOCALETYPEDICT = {
    constants.LOCALE_DEFAULT: Default(),
    constants.LOCALE_SE_GOTHENBURG: SE_Gothenburg(),
    constants.LOCALE_SE_PARTILLE: SE_Partille(),
    constants.LOCALE_SE_KARLSTAD: SE_Karlstad(),
    constants.LOCALE_SE_KRISTINEHAMN: SE_Kristinehamn(),
    constants.LOCALE_SE_NACKA_NORMAL: SE_Nacka_normal(),
    constants.LOCALE_SE_MALUNG_SALEN: SE_Malung_Salen(),
    constants.LOCALE_SE_SALA: SE_Sala(),
    constants.LOCALE_SE_SKOVDE: SE_Skovde(),
}

class LocaleData:
    def __init__(self, input, domain):
        self._data = None
        self._type = input
        self._domain = domain

        self._data = LOCALETYPEDICT[input]

        # if input == constants.LOCALE_SE_GOTHENBURG:
        #     self._data = SE_Gothenburg()
        # elif input == constants.LOCALE_SE_PARTILLE:
        #     self._data = SE_Partille()
        # elif input == constants.LOCALE_SE_KARLSTAD:
        #     self._data = SE_Karlstad()
        # elif input == constants.LOCALE_SE_KRISTINEHAMN:
        #     self._data = SE_Kristinehamn()
        # elif input == constants.LOCALE_SE_NACKA_NORMAL:
        #     self._data = SE_Nacka_normal()
        # elif input == constants.LOCALE_DEFAULT:
        #     self._data = Default()

    @property
    def type(self) -> str:
        return self._type

    @property
    def data(self):
        return self._data

    @property
    def current_peak_entity(self) -> str:
        return f"sensor.{self._domain}_{ex.nametoid(PeaqSQLSensorHelper('').getquerytype(self.data.observed_peak)[constants.NAME])}"


