import logging

from homeassistant.core import HomeAssistant
from peaqevcore.locale_service.Locale import LOCALETYPEDICT

_LOGGER = logging.getLogger(__name__)

class LocaleData:
    def __init__(self, input_type, domain, hass: HomeAssistant):
        self._data = None
        self._type = input_type
        self._domain = domain
        self._hass = hass

        self._data = LOCALETYPEDICT[input_type]

    @property
    def type(self) -> str:
        return self._type

    @property
    def data(self):
        return self._data
