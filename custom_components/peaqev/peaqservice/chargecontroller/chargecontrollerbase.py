import logging
import time
from abc import abstractmethod
from datetime import datetime, timedelta

from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class ChargeControllerBase():
    DONETIMEOUT = 180
    DEBUGLOG_TIMEOUT = 60

    def __init__(self, hub):
        super().__init__()
        self._hub = hub
        self.name: str = f"{self._hub.hubname} {CHARGERCONTROLLER}"
        self._status_type: ChargeControllerStates = ChargeControllerStates.Idle
        self._initalized: bool = False
        self._latestchargerstart = time.time()
        self._latest_debuglog = 0

    @property
    def status_type(self) -> ChargeControllerStates:
        return self._status_type

    @status_type.setter
    def status_type(self, val) -> None:
        if val != self._status_type:
            self._status_type = val

    @property
    def latest_charger_start(self) -> float:
        return self._latestchargerstart

    @latest_charger_start.setter
    def latest_charger_start(self, val):
        self._latestchargerstart = val

    @property
    def status(self) -> str:
        ret = ChargeControllerStates.Error
        if not self._hub.is_initialized:
            return "Hub not ready. Check logs!"
        if self._hub.is_initialized and not self._initalized:
            self._initalized = True
            self.__debug_log("Chargecontroller is initialized and ready to work!")
        if self._hub.chargertype.options.charger_is_outlet:
            ret = self._get_status_outlet()
        else:
            ret = self._get_status()
        if ret == ChargeControllerStates.Error:
            _LOGGER.error(
                f"Chargecontroller returned faulty state. Charger reported {self._hub.sensors.chargerobject.value} as state.")
        self._status_type = ret
        return ret.name

    @property
    def non_hours_display_model(self) -> list:
        ret = []
        for i in self._hub.non_hours:
            if i < datetime.now().hour and len(self._hub.hours.prices_tomorrow) > 0:
                ret.append(f"{str(i)}⁺¹")
            elif i >= datetime.now().hour:
                ret.append(str(i))
        return ret

    @property
    def caution_hours_display_model(self) -> dict:
        ret = {}
        if len(self._hub.dynamic_caution_hours) > 0:
            for h in self._hub.dynamic_caution_hours:
                if h < datetime.now().hour:
                    hh = f"{h}⁺¹"
                else:
                    hh = h
                ret[hh] = f"{str((int(self._hub.dynamic_caution_hours[h] * 100)))}%"
        return ret

    @property
    def current_charge_permittance_display_model(self) -> str:
        ret = 100
        hour = datetime.now().hour
        if hour in self._hub.non_hours:
            ret = 0
        elif hour in self._hub.dynamic_caution_hours.keys():
            ret = int(self._hub.dynamic_caution_hours[hour] * 100)
        return f"{str(ret)}%"

    @property
    def state_display_model(self) -> str:
        hour = datetime.now().hour
        ret = "Charging allowed"
        if self._hub.svk.should_stop:
            return self._hub.svk.stopped_string
        if self._hub.timer.is_override:
            return self._hub.timer.override_string
        if hour in self._hub.non_hours:
            ret = self._calculate_stop_len(self._hub.non_hours)
        elif hour in self._hub.dynamic_caution_hours.keys():
            val = self._hub.dynamic_caution_hours[hour]
            ret = f"Charging allowed at {int(val * 100)}% of peak"
        return ret

    def _get_status_outlet(self) -> ChargeControllerStates:
        ret = ChargeControllerStates.Error
        update_timer = False
        free_charge = self._hub.sensors.locale.data.free_charge(self._hub.sensors.locale.data)

        if self._hub.svk.should_stop:
            """interim fix for svk peak hours"""
            update_timer = True
            ret = ChargeControllerStates.Stop
        elif self._hub.sensors.charger_enabled.value is False:
            update_timer = True
            ret = ChargeControllerStates.Disabled
        elif self._hub.sensors.charger_done.value is True:
            ret = ChargeControllerStates.Done
        elif datetime.now().hour in self._hub.non_hours and free_charge is False and self._hub.timer.is_override is False:
            update_timer = True
            ret = ChargeControllerStates.Stop
        elif self._hub.chargertype.entities.powerswitch == "on" and self._hub.chargertype.entities.powermeter < 1:
            ret = self._get_status_connected()
            update_timer = (ret == ChargeControllerStates.Stop)
        else:
            ret = self._get_status_charging()
            update_timer = True
        if update_timer is True:
            self.latest_charger_start = time.time()
        return ret

    def _get_status(self) -> ChargeControllerStates:
        ret = ChargeControllerStates.Error
        update_timer = True
        _state = self._hub.sensors.chargerobject.value.lower()
        free_charge = self._hub.sensors.locale.data.free_charge(self._hub.sensors.locale.data)
        if self._hub.sensors.charger_enabled.value is False:
            ret = ChargeControllerStates.Disabled
        elif _state in self._hub.chargertype.chargerstates[ChargeControllerStates.Done]:
            self._hub.sensors.charger_done.value = True
            ret = ChargeControllerStates.Done
            update_timer = False
        elif _state in self._hub.chargertype.chargerstates[ChargeControllerStates.Idle]:
            ret = ChargeControllerStates.Idle
            if self._hub.sensors.charger_done.value is True:
                self._hub.sensors.charger_done.value = False
        elif self._hub.sensors.power.killswitch.is_dead:
            ret = ChargeControllerStates.Error
        elif _state not in self._hub.chargertype.chargerstates[
            ChargeControllerStates.Idle] and self._hub.sensors.charger_done.value is True:
            ret = ChargeControllerStates.Done
            update_timer = False
        elif datetime.now().hour in self._hub.non_hours and free_charge is False and self._hub.timer.is_override is False:
            ret = ChargeControllerStates.Stop
        elif self._hub.svk.should_stop:
            """interim fix for svk peak hours"""
            ret = ChargeControllerStates.Stop
        elif _state in self._hub.chargertype.chargerstates[ChargeControllerStates.Connected]:
            ret = self._get_status_connected(_state)
            update_timer = (ret == ChargeControllerStates.Stop)
        elif _state in self._hub.chargertype.chargerstates[ChargeControllerStates.Charging]:
            ret = self._get_status_charging()
        if update_timer is True:
            self.latest_charger_start = time.time()
        return ret

    def _is_done(self, charger_state) -> bool:
        if len(self._hub.chargertype.chargerstates[ChargeControllerStates.Done]) > 0:
            _states_test = charger_state in self._hub.chargertype.chargerstates[ChargeControllerStates.Done]
            if _states_test:
                self.__debug_log(f"'is_done' reported that charger is Done based on current charger state")
            return _states_test
        _regular_test = time.time() - self.latest_charger_start > self.DONETIMEOUT
        if _regular_test:
            self.__debug_log(
                f"'is_done' reported that charger is Done because of idle-charging for more than {self.DONETIMEOUT} seconds.")
        return _regular_test

    def __debug_log(self, message: str):
        if time.time() - self._latest_debuglog > self.DEBUGLOG_TIMEOUT:
            _LOGGER.debug(message)
            self._latest_debuglog = time.time()

    @staticmethod
    def _defer_start(non_hours: list) -> bool:
        """Defer starting if next hour is a non-hour and minute is 50 or greater, to avoid short running times."""
        if (datetime.now() + timedelta(hours=1)).hour in non_hours:
            return datetime.now().minute >= 50
        return False

    @abstractmethod
    def _get_status_charging(self) -> ChargeControllerStates:
        pass

    @abstractmethod
    def _get_status_connected(self, charger_state=None) -> ChargeControllerStates:
        pass

    @staticmethod
    def _get_stopped_string(h) -> str:
        val = h + 1 if h + 1 < 24 else h + 1 - 24
        if len(str(val)) == 1:
            return f"Charging stopped until 0{val}:00"
        return f"Charging stopped until {val}:00"

    @staticmethod
    def _getuneven(first, second) -> bool:
        if second > first:
            return first - (second - 24) != 1
        return first - second != 1

    @staticmethod
    def _calculate_stop_len(nonhours) -> str:
        ret = ""
        for idx, h in enumerate(nonhours):
            if idx + 1 < len(nonhours):
                if ChargeControllerBase._getuneven(nonhours[idx + 1], nonhours[idx]):
                    ret = ChargeControllerBase._get_stopped_string(h)
                    break
            elif idx + 1 == len(nonhours):
                ret = ChargeControllerBase._get_stopped_string(h)
                break
        return ret
