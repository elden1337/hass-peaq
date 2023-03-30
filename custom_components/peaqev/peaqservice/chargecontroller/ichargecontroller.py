import logging
import time
from abc import abstractmethod
from datetime import datetime

from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_helpers import calculate_stop_len
from custom_components.peaqev.peaqservice.chargecontroller.const import (
    DONETIMEOUT, DEBUGLOG_TIMEOUT, CHARGING_ALLOWED
)
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER
from custom_components.peaqev.peaqservice.util.extensionmethods import dt_from_epoch, log_once

_LOGGER = logging.getLogger(__name__)
import asyncio

class IChargeController:
    def __init__(self, hub, charger_states):
        self.hub = hub
        self.name: str = f"{self.hub.hubname} {CHARGERCONTROLLER}"
        self._status_type: ChargeControllerStates = ChargeControllerStates.Idle
        self._is_initalized: bool = False
        self._latest_charger_start: float = time.time()
        self._latest_debuglog = 0
        self._charger_states: dict = charger_states
        self._lock = asyncio.Lock()
        self.hub.observer.add("update latest charger start", self._update_latest_charger_start)
        self.hub.observer.add("hub initialized", self._do_initialize)

    @property
    def status_type(self) -> ChargeControllerStates:
        return self._status_type

    @status_type.setter
    def status_type(self, val) -> None:
        self._status_type = val

    @property
    def latest_charger_start(self) -> str:
        """For Lovelace-purposes. Converts and returns epoch-timer to readable datetime-string"""
        return dt_from_epoch(self._latest_charger_start)

    def _update_latest_charger_start(self, val):
        if self.hub.enabled:
            self._latest_charger_start = val

    def async_update_latest_charger_start(self, val):
        if self.hub.enabled:
            self._latest_charger_start = val

    @property
    def is_initialized(self) -> bool:
        if not self.hub.is_initialized:
            return False
        if self.hub.is_initialized and not self._is_initalized:
            self._do_initialize()
        return self._is_initalized

    @property
    def non_hours_display_model(self) -> list:
        ret = []
        for i in self.hub.non_hours:
            if i < datetime.now().hour and len(self.hub.prices_tomorrow) > 0:
                ret.append(f"{str(i)}⁺¹")
            elif i >= datetime.now().hour:
                ret.append(str(i))
        return ret

    @property
    def caution_hours_display_model(self) -> dict:
        ret = {}
        if len(self.hub.dynamic_caution_hours) > 0:
            for h in self.hub.dynamic_caution_hours:
                if h < datetime.now().hour:
                    hh = f"{h}⁺¹"
                else:
                    hh = h
                ret[hh] = f"{str((int(self.hub.dynamic_caution_hours[h] * 100)))}%"
        return ret

    @property
    def current_charge_permittance_display_model(self) -> str:
        ret = 100
        hour = datetime.now().hour
        if hour in self.hub.non_hours:
            ret = 0
        elif hour in self.hub.dynamic_caution_hours.keys():
            ret = int(self.hub.dynamic_caution_hours.get(hour) * 100)
        return f"{str(ret)}%"

    @property
    def state_display_model(self) -> str:
        hour = datetime.now().hour
        ret = CHARGING_ALLOWED.capitalize()
        if self.hub.timer.is_override:  # todo: composition
            return self.hub.timer.override_string  # todo: composition
        if hour in self.hub.non_hours:
            ret = calculate_stop_len(self.hub.non_hours)
        elif hour in self.hub.dynamic_caution_hours.keys():
            val = self.hub.dynamic_caution_hours.get(hour)
            ret += f" at {int(val * 100)}% of peak"
        return ret

    def _do_initialize(self) -> None:
        self._is_initalized = True
        log_once("Chargecontroller is initialized and ready to work.")

    def _check_initialized(self) -> bool:
        if not self.hub.options.peaqev_lite:
            _state = self.hub.get_power_sensor_from_hass()
            if _state is not None:
                if isinstance(_state, (float, int)):
                    return True
            return False
        return True

    async def async_set_status(self) -> None:
        ret = ChargeControllerStates.Error
        match self.hub.chargertype.type:
            case ChargerType.Outlet:
                ret = await self.async_get_status_outlet()
            case ChargerType.NoCharger:
                ret = await self.async_get_status_no_charger()
            case _:
                ret = await self.async_get_status()
        async with self._lock:
            if ret != self.status_type:
                self.status_type = ret
                await self.hub.observer.async_broadcast("chargecontroller status changed", ret)

    async def async_get_status(self) -> ChargeControllerStates:
        _state = await self.hub.async_get_chargerobject_value()
        ret = ChargeControllerStates.Error
        update_timer = True
        if not self.hub.enabled:
            ret = ChargeControllerStates.Disabled
        elif _state in self._charger_states.get(ChargeControllerStates.Done):
            self.hub.observer.broadcast("update charger done", True)
            ret = ChargeControllerStates.Done
            update_timer = False
        elif _state in self._charger_states.get(ChargeControllerStates.Idle):
            ret = ChargeControllerStates.Idle
            if self.hub.charger_done:
                self.hub.observer.broadcast("update charger done", False)
        elif self.hub.sensors.power.killswitch.is_dead:  # todo: composition
            ret = ChargeControllerStates.Error
        elif _state not in self._charger_states.get(ChargeControllerStates.Idle) and self.hub.charger_done:
            ret = ChargeControllerStates.Done
            update_timer = False
        elif datetime.now().hour in self.hub.non_hours and not self.hub.timer.is_override:  # todo: composition
            ret = ChargeControllerStates.Stop
        elif _state in self._charger_states.get(ChargeControllerStates.Connected):
            ret = await self.async_get_status_connected(_state)
            update_timer = (ret == ChargeControllerStates.Stop)
        elif _state in self._charger_states.get(ChargeControllerStates.Charging):
            ret = await self.async_get_status_charging()
        if update_timer:
            await self.async_update_latest_charger_start(time.time())
        if ret == ChargeControllerStates.Error:
            _LOGGER.error(
                f"Chargecontroller returned faulty state. Charger reported {_state} as state.")
        return ret

    async def async_get_status_outlet(self) -> ChargeControllerStates:
        ret = ChargeControllerStates.Error
        update_timer = True
        if not self.hub.enabled:
            ret = ChargeControllerStates.Disabled
        elif self.hub.charger_done:
            return ChargeControllerStates.Done
        elif datetime.now().hour in self.hub.non_hours and self.hub.timer.is_override is False:  # todo: composition
            ret = ChargeControllerStates.Stop
        elif self.hub.chargertype.entities.powerswitch == "on" and self.hub.chargertype.entities.powermeter < 1:  # todo: composition
            ret = await self.async_get_status_connected()
            update_timer = (ret == ChargeControllerStates.Stop)
        else:
            ret = await self.async_get_status_charging()
        if update_timer:
            await self.async_update_latest_charger_start(time.time())
        return ret

    async def async_get_status_no_charger(self) -> ChargeControllerStates:
        ret = ChargeControllerStates.Error
        if not self.hub.enabled:
            ret = ChargeControllerStates.Disabled
        elif datetime.now().hour in self.hub.non_hours and not self.hub.timer.is_override:
            ret = ChargeControllerStates.Stop
        else:
            ret = ChargeControllerStates.Start
        await self.async_update_latest_charger_start(time.time())
        return ret

    async def async_is_done(self, charger_state) -> bool:
        ret = False
        if len(self._charger_states.get(ChargeControllerStates.Done)) > 0:
            if charger_state in self._charger_states.get(ChargeControllerStates.Done):
                self.__debug_log(f"'is_done' reported that charger is Done based on current charger state")
                ret = True
        elif time.time() - self._latest_charger_start > DONETIMEOUT:
            self.__debug_log(
                f"'is_done' reported that charger is Done because of idle-charging for more than {DONETIMEOUT} seconds.")
            ret = True
        if ret and self.hub.sensors.charger_done is False:
            await self.hub.observer.async_broadcast("update charger done", True)
        return ret

    def __debug_log(self, message: str):
        if time.time() - self._latest_debuglog > DEBUGLOG_TIMEOUT:
            _LOGGER.debug(message)
            self._latest_debuglog = time.time()

    @property
    @abstractmethod
    def below_startthreshold(self) -> bool:
        pass

    @property
    @abstractmethod
    def above_stopthreshold(self) -> bool:
        pass

    @property
    @abstractmethod
    def status_string(self) -> str:
        pass

    @abstractmethod
    async def async_get_status_charging(self) -> ChargeControllerStates:
        pass

    @abstractmethod
    async def async_get_status_connected(self, charger_state=None) -> ChargeControllerStates:
        pass
