import asyncio
import logging
import time
from abc import abstractmethod
from datetime import datetime

from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_helpers import calculate_stop_len
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER
from custom_components.peaqev.peaqservice.util.extensionmethods import dt_from_epoch

_LOGGER = logging.getLogger(__name__)

DONETIMEOUT = 180
DEBUGLOG_TIMEOUT = 60
INITIALIZING = "Initializing..."


class IChargeController:
    def __init__(self, hub, charger_states):
        self.hub = hub
        self.name: str = f"{self.hub.hubname} {CHARGERCONTROLLER}"
        self._status_type: ChargeControllerStates = ChargeControllerStates.Idle
        self._is_initalized: bool = False
        self._latest_charger_start: float = time.time()
        self._latest_debuglog = 0
        self._charger_states: dict = charger_states
        self.hub.observer.add("update latest charger start", self._update_latest_charger_start)
        self.hub.observer.add("hub initialized", self._do_initialize)

    @property
    def status_type(self) -> ChargeControllerStates:
        return self._status_type

    @status_type.setter
    def status_type(self, val) -> None:
        if val != self._status_type:
            self._status_type = val
            self.hub.observer.broadcast("chargecontroller status changed", self._status_type)

    @property
    def latest_charger_start(self) -> str:
        """For Lovelace-purposes. Converts and returns epoch-timer to readable datetime-string"""
        return dt_from_epoch(self._latest_charger_start)

    async def _update_latest_charger_start(self, val):
        if self.hub.enabled:
            setattr(self, "_latest_charger_start", val)

    @property
    def status_string(self) -> str:
        if not self.is_initialized:
            return INITIALIZING
        return asyncio.run_coroutine_threadsafe(
            self._get_status_string(), self.hub.state_machine.loop
        ).result()

    async def _get_status_string(self):
        ret = ChargeControllerStates.Error
        match self.hub.chargertype.type:
            case ChargerType.Outlet:
                ret = await self._get_status_outlet()
            case ChargerType.NoCharger:
                ret = await self._get_status_no_charger()
            case _:
                ret = await self._get_status()
        self.status_type = ret
        return ret.name

    @property
    def is_initialized(self) -> bool:
        if not self.hub.is_initialized:
            return False
        return self._do_initialize()

    def _do_initialize(self):
        if self.hub.is_initialized and not self._is_initalized:
            self._is_initalized = self._check_initialized()
            if self._is_initalized:
                _LOGGER.info("Chargecontroller is initialized and ready to work!")
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
        ret = "Charging allowed"
        if self.hub.timer.is_override:  # todo: composition
            return self.hub.timer.override_string  # todo: composition
        if hour in self.hub.non_hours:
            ret = calculate_stop_len(self.hub.non_hours)
        elif hour in self.hub.dynamic_caution_hours.keys():
            val = self.hub.dynamic_caution_hours.get(hour)
            ret = f"Charging allowed at {int(val * 100)}% of peak"
        return ret

    def _check_initialized(self) -> bool:
        if not self.hub.options.peaqev_lite:
            _state = self.hub.get_power_sensor_from_hass()
            if _state is not None:
                if isinstance(_state, (float,int)):
                    return True
            return False
        return True

    async def _get_status_outlet(self) -> ChargeControllerStates:
        ret = ChargeControllerStates.Error
        update_timer = False

        if not self.hub.enabled:
            update_timer = True
            ret = ChargeControllerStates.Disabled
        elif self.hub.charger_done:
            ret = ChargeControllerStates.Done
        elif datetime.now().hour in self.hub.non_hours and self.hub.timer.is_override is False:  # todo: composition
            update_timer = True
            ret = ChargeControllerStates.Stop
        elif self.hub.chargertype.entities.powerswitch == "on" and self.hub.chargertype.entities.powermeter < 1:  # todo: composition
            ret = await self._get_status_connected()
            update_timer = (ret == ChargeControllerStates.Stop)
        else:
            ret = await self._get_status_charging()
            update_timer = True
        if update_timer is True:
            await self._update_latest_charger_start(time.time())
        return ret

    async def _get_status(self) -> ChargeControllerStates:
        _state = await self.hub.get_chargerobject_value()
        ret = ChargeControllerStates.Error
        update_timer = True

        if not self.hub.enabled:
            ret = ChargeControllerStates.Disabled
        elif _state in self._charger_states.get(ChargeControllerStates.Done):
            await self.hub.observer.async_broadcast("update charger done", True)
            ret = ChargeControllerStates.Done
            update_timer = False
        elif _state in self._charger_states.get(ChargeControllerStates.Idle):
            ret = ChargeControllerStates.Idle
            if self.hub.charger_done:
                await self.hub.observer.async_broadcast("update charger done", False)
        elif self.hub.sensors.power.killswitch.is_dead:  # todo: composition
            ret = ChargeControllerStates.Error
        elif _state not in self._charger_states.get(ChargeControllerStates.Idle) and self.hub.charger_done:
            ret = ChargeControllerStates.Done
            update_timer = False
        elif datetime.now().hour in self.hub.non_hours and not self.hub.timer.is_override:  # todo: composition
            ret = ChargeControllerStates.Stop
        elif _state in self._charger_states.get(ChargeControllerStates.Connected):
            ret = await self._get_status_connected(_state)
            update_timer = (ret == ChargeControllerStates.Stop)
        elif _state in self._charger_states.get(ChargeControllerStates.Charging):
            ret = await self._get_status_charging()

        if update_timer:
            await self._update_latest_charger_start(time.time())

        if ret == ChargeControllerStates.Error:
            _LOGGER.error(f"Chargecontroller returned faulty state. Charger reported {self.hub.get_chargerobject_value()} as state.")
        return ret

    async def _get_status_no_charger(self) -> ChargeControllerStates:
        ret = ChargeControllerStates.Error
        update_timer = True

        if not self.hub.enabled:
            ret = ChargeControllerStates.Disabled
        elif datetime.now().hour in self.hub.non_hours and not self.hub.timer.is_override:
            ret = ChargeControllerStates.Stop
        else:
            ret = ChargeControllerStates.Start
        if update_timer:
            await self._update_latest_charger_start(time.time())
        return ret

    async def _is_done(self, charger_state) -> bool:
        ret = False
        if len(self._charger_states.get(ChargeControllerStates.Done)) > 0:
            _states_test = charger_state in self._charger_states.get(ChargeControllerStates.Done)
            if _states_test:
                await self.__debug_log(f"'is_done' reported that charger is Done based on current charger state")
                ret = _states_test
        _regular_test = time.time() - self._latest_charger_start > DONETIMEOUT
        if _regular_test:
            await self.__debug_log(
                f"'is_done' reported that charger is Done because of idle-charging for more than {DONETIMEOUT} seconds.")
            ret = _regular_test
        if ret and self.hub.sensors.charger_done is False:
            await self.hub.observer.async_broadcast("update charger done", True)
        return ret

    async def __debug_log(self, message: str):
        if time.time() - self._latest_debuglog > DEBUGLOG_TIMEOUT:
            _LOGGER.debug(message)
            self._latest_debuglog = time.time()

    @abstractmethod
    async def _get_status_charging(self) -> ChargeControllerStates:
        pass

    @abstractmethod
    async def _get_status_connected(self, charger_state=None) -> ChargeControllerStates:
        pass
