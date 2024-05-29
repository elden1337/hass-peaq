import logging
from datetime import datetime

from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade

_LOGGER = logging.getLogger(__name__)

class EventProperty:
    def __init__(self, name, prop_type: type, hass: IHomeAssistantFacade, default=None):
        self._value = default
        self._hass = hass
        self.name = name
        self._timeout = None
        self._prop_type = prop_type

    @property
    def value(self):
        if self._prop_type == bool:
            if self._value and self._is_timeout():
                self._value = False
        return self._value

    @value.setter
    def value(self, val):
        if self._value != val:
            self._value = val
            self._hass.bus_fire(f'peaqev.{self.name}', {'new': val})
            _LOGGER.debug(f'EventProperty peaqev.{self.name} changed to {val}')

    def _is_timeout(self) -> bool:
        if self._timeout is None:
            return False
        return self._timeout < datetime.now()

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, val: datetime|None):
        self._timeout = val
