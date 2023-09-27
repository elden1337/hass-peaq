import logging
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

@dataclass
class ChargerModel:
    running: bool = False
    disable_current_updates: bool = False
    _session_active: bool = False
    latest_charger_call: float = 0
    lastest_call_off: float = 0
    unsuccessful_stop: bool = False

    @property
    def session_active(self) -> bool:
        return self._session_active

    @session_active.setter
    def session_active(self, val: bool) -> None:
        if val != self._session_active:
            _LOGGER.debug(f"Setting session_active to {val}")
            self._session_active = val
