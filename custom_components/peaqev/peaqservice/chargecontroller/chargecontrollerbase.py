import logging
import time
from abc import abstractmethod
from peaqevcore.Models import CHARGERSTATES
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class ChargeControllerBase:
    DONETIMEOUT = 180

    def __init__(self, hub):
        self._hub = hub
        self.name = f"{self._hub.hubname} {CHARGERCONTROLLER}"
        self._status = CHARGERSTATES.Idle
        self._latestchargerstart = time.time()

    @property
    def latest_charger_start(self) -> float:
        return self._latestchargerstart

    @latest_charger_start.setter
    def latest_charger_start(self, val):
        self._latestchargerstart = val

    @property
    def status(self):
        return self._get_status()

    def update_latestchargerstart(self):
        self.latest_charger_start = time.time()

    @abstractmethod
    def _get_status(self):
        pass