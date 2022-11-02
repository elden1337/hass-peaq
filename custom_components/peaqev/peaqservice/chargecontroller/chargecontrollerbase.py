import logging
import time
from abc import abstractmethod
from datetime import datetime

from peaqevcore.models.chargerstates import CHARGERSTATES

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
    def status(self) -> str:
        if self._hub.is_initialized is False:
            return "Hub not ready. Check logs!"
        if self._hub.is_initialized is True:
            if self._chargecontroller_initalized is False:
                self._chargecontroller_initalized = True
                _LOGGER.debug("Chargecontroller is initialized and ready to work!")
        if self._hub.chargertype.charger.options.charger_is_outlet is True:
            ret = self._get_status_outlet()
        else:
            ret = self._get_status()
        if ret == CHARGERSTATES.Error:
            _LOGGER.error(f"Chargecontroller returned faulty state. Charger reported {self._hub.sensors.chargerobject.value} as state.")
        return ret.name

    def update_latestchargerstart(self):
        self.latest_charger_start = time.time()

    def _get_status_outlet(self) -> CHARGERSTATES:
        ret = CHARGERSTATES.Error
        update_timer = False
        free_charge = self._hub.sensors.locale.data.free_charge(self._hub.sensors.locale.data)

        if self._hub.sensors.charger_enabled.value is False:
            update_timer = True
            ret = CHARGERSTATES.Disabled
        elif self._hub.sensors.charger_done.value is True:
            ret = CHARGERSTATES.Done
        elif datetime.now().hour in self._hub.non_hours and free_charge is False and self._hub.timer.is_override is False:
            update_timer = True
            ret = CHARGERSTATES.Stop
        elif self._hub.chargertype.charger.entities.powerswitch == "on" and self._hub.chargertype.charger.entities.powermeter < 1:
            ret = self._get_status_connected()
            update_timer = (ret == CHARGERSTATES.Stop)
        else:
            ret = self._get_status_charging()
            update_timer = True

        if update_timer is True:
            self.update_latestchargerstart()
        return ret

    def _get_status(self) -> CHARGERSTATES:
        ret = CHARGERSTATES.Error
        update_timer = True
        _state = self._hub.sensors.chargerobject.value.lower()
        free_charge = self._hub.sensors.locale.data.free_charge(self._hub.sensors.locale.data)

        if self._hub.sensors.charger_enabled.value is False:
            ret = CHARGERSTATES.Disabled
        elif _state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Done]:
            self._hub.sensors.charger_done.value = True
            ret = CHARGERSTATES.Done
            update_timer = False
        elif _state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Idle]:
            ret = CHARGERSTATES.Idle
            if self._hub.sensors.charger_done.value is True:
                self._hub.sensors.charger_done.value = False
        elif self._hub.sensors.power.killswitch.is_dead:
            ret = CHARGERSTATES.Error
        elif _state not in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Idle] and self._hub.sensors.charger_done.value is True:
            ret = CHARGERSTATES.Done
            update_timer = False
        elif datetime.now().hour in self._hub.non_hours and free_charge is False and self._hub.timer.is_override is False:
            ret = CHARGERSTATES.Stop
        elif _state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Connected]:
            ret = self._get_status_connected(_state)
            update_timer = (ret == CHARGERSTATES.Stop)
        elif _state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Charging]:
            ret = self._get_status_charging()

        if update_timer is True:
            self.update_latestchargerstart()
        return ret

    def _is_done(self, charger_state) -> bool:
        if len(self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Done]) > 0:
            _states_test = charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Done]
            if _states_test:
                _LOGGER.debug(f"'is_done' reported that charger is Done based on current charger state")
            return _states_test
        _regular_test = time.time() - self.latest_charger_start > self.DONETIMEOUT
        if _regular_test:
            _LOGGER.debug(f"'is_done' reported that charger is Done because of idle-charging for more than {self.DONETIMEOUT} seconds.")
        return _regular_test

    @abstractmethod
    def _get_status_charging(self) -> CHARGERSTATES:
        pass

    @abstractmethod
    def _get_status_connected(self, charger_state=None) -> CHARGERSTATES:
        pass
