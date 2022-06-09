import logging
import time
from abc import abstractmethod
from datetime import datetime

from peaqevcore.Models import CHARGERSTATES

from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class ChargeControllerBase:
    DONETIMEOUT = 180

    def __init__(self, hub):
        self._hub = hub
        self.name = f"{self._hub.hubname} {CHARGERCONTROLLER}"
        self._status = CHARGERSTATES.Idle
        self._chargecontroller_initalized = False
        self._latestchargerstart = time.time()

    @property
    def latest_charger_start(self) -> float:
        return self._latestchargerstart

    @latest_charger_start.setter
    def latest_charger_start(self, val):
        self._latestchargerstart = val

    @property
    def status(self):
        if self._hub.is_initialized is False:
            return "Hub not ready. Check logs!"
        if self._hub.is_initialized is True:
            if self._chargecontroller_initalized is False:
                self._chargecontroller_initalized = True
                _LOGGER.info("Chargecontroller is initialized and ready to work!")
        ret = self._get_status()
        if ret == CHARGERSTATES.Error:
            msg = f"Chargecontroller returned faulty state. Charger reported {self._hub.chargerobject.value.lower()} as state."
            _LOGGER.error(msg)
        return ret.name

    def update_latestchargerstart(self):
        self.latest_charger_start = time.time()

    def _get_status(self):
        ret = CHARGERSTATES.Error
        update_timer = False
        charger_state = self._hub.chargerobject.value.lower()
        free_charge = self._hub.locale.data.free_charge(self._hub.locale.data)

        if charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Done]:
            self._hub.charger_done.value = True
            ret = CHARGERSTATES.Done
        elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Idle]:
            update_timer = True
            ret = CHARGERSTATES.Idle
            if self._hub.charger_done.value is True:
                self._hub.charger_done.value = False
        elif charger_state in self._hub.chargertype.charger.chargerstates[
            CHARGERSTATES.Connected] and self._hub.charger_enabled.value is False:
            update_timer = True
            ret = CHARGERSTATES.Connected
        elif charger_state not in self._hub.chargertype.charger.chargerstates[
            CHARGERSTATES.Idle] and self._hub.charger_done.value is True:
            ret = CHARGERSTATES.Done
        elif datetime.now().hour in self._hub.hours.non_hours and free_charge is False:
            update_timer = True
            ret = CHARGERSTATES.Stop

        elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Connected]:
            ret = self._get_status_connected()
            update_timer = (ret == CHARGERSTATES.Stop)

        elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Charging]:
            ret = self._get_status_charging()
            update_timer = True

        if update_timer is True:
            self.update_latestchargerstart()
        return ret

    @abstractmethod
    def _get_status_charging(self) -> CHARGERSTATES:
        pass

    @abstractmethod
    def _get_status_connected(self) -> CHARGERSTATES:
        pass
