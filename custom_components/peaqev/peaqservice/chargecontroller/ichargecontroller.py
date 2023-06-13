import logging
import time
from abc import abstractmethod
from datetime import datetime
from typing import Tuple

from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.services.session.session import Session

from custom_components.peaqev.peaqservice.chargecontroller.charger.charger import \
    Charger
from custom_components.peaqev.peaqservice.chargecontroller.charger.savings_controller import \
    SavingsController
from custom_components.peaqev.peaqservice.chargecontroller.chargercontroller_model import \
    ChargeControllerModel
from custom_components.peaqev.peaqservice.chargecontroller.const import (
    DEBUGLOG_TIMEOUT, DONETIMEOUT)
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.util.constants import \
    CHARGERCONTROLLER
from custom_components.peaqev.peaqservice.util.extensionmethods import log_once

_LOGGER = logging.getLogger(__name__)


class IChargeController:
    """The interface for the charge controller"""

    def __init__(self, hub, charger_states, charger_type):
        self.hub = hub
        self.name: str = f"{self.hub.hubname} {CHARGERCONTROLLER}"
        self.model = ChargeControllerModel(
            charger_type=charger_type, charger_states=charger_states
        )
        self.charger = Charger(controller=self)
        self.session = Session(self.charger)
        self.savings = SavingsController(self)
        self._setup_observers()

    async def async_setup(self):
        await self.session.async_setup()
        await self.charger.async_setup()

    @property
    def status_type(self) -> ChargeControllerStates:
        return self.model.status_type

    @property
    def connected(self) -> bool:
        return self.status_type not in [
            ChargeControllerStates.Idle,
            ChargeControllerStates.Disabled,
            ChargeControllerStates.Error,
        ]

    @property
    def is_initialized(self) -> bool:
        if not self.hub.is_initialized:
            return False
        if self.hub.options.price.price_aware and not self.hub.nordpool.is_initialized:
            return False
        if self.hub.is_initialized and not self.model.is_initialized:
            return self._check_initialized()
        return self.model.is_initialized

    async def async_update_latest_charger_start(self):
        if self.hub.enabled:
            self.model.latest_charger_start = time.time()

    def _do_initialize(self) -> bool:
        self.model.is_initialized = True
        log_once("Chargecontroller is initialized and ready to work.")
        self.model.latest_charger_start = time.time()
        return self.model.is_initialized

    def _check_initialized(self) -> bool:
        if self.model.is_initialized:
            return True
        if not self.hub.options.peaqev_lite:
            _state = self.hub.get_power_sensor_from_hass()
            if _state is not None:
                if isinstance(_state, (float, int)):
                    if _state > 0:
                        return self._do_initialize()
            return False
        return self._do_initialize()

    async def async_set_status(self) -> None:
        try:
            if self.is_initialized:
                ret: ChargeControllerStates
                update_timer: bool = False
                try:
                    match self.model.charger_type:
                        case ChargerType.Outlet:
                            ret, update_timer = await self.async_get_status_outlet()
                        case ChargerType.NoCharger:
                            ret, update_timer = await self.async_get_status_no_charger()
                        case _:
                            ret, update_timer = await self.async_get_status()
                except Exception as e:
                    _LOGGER.debug(f"Error in async_set_status1: {e}")
                    ret = ChargeControllerStates.Error
                if update_timer is True:
                    await self.async_update_latest_charger_start()
                await self.async_set_status_type(ret)
        except Exception as e:
            _LOGGER.debug(f"Error in async_set_status2: {e}")

    async def async_set_status_type(self, status_type: ChargeControllerStates) -> None:
        try:
            if isinstance(status_type, ChargeControllerStates):
                if status_type != self.status_type:
                    await self.async_check_broadcasting(
                        old_state=self.status_type, new_state=status_type
                    )
                    self.model.status_type = status_type
                    if self.model.charger_type is not ChargerType.NoCharger:
                        await self.charger.async_charge()
        except Exception as e:
            _LOGGER.debug(f"Error in async_set_status_type: {e}")

    async def async_check_broadcasting(
        self, old_state: ChargeControllerStates, new_state: ChargeControllerStates
    ) -> None:
        _LOGGER.debug(f"async_check_broadcasting: {old_state} -> {new_state}")
        match new_state:
            case ChargeControllerStates.Idle:
                await self.hub.observer.async_broadcast("car disconnected")
                if self.hub.charger_done:
                    await self.hub.observer.async_broadcast(
                        "update charger done", False
                    )
            case ChargeControllerStates.Done:
                await self.hub.observer.async_broadcast("update charger done", True)
            case ChargeControllerStates.Charging | ChargeControllerStates.Start | ChargeControllerStates.Stop | ChargeControllerStates.Connected:
                if old_state in [
                    ChargeControllerStates.Idle,
                    ChargeControllerStates.Disabled,
                ]:
                    await self.hub.observer.async_broadcast("car connected")
            case _:
                pass

    async def async_get_status(self) -> Tuple[ChargeControllerStates, bool]:
        _state = await self.hub.async_request_sensor_data("chargerobject_value")
        try:
            if not self.hub.enabled:
                if _state in self.model.charger_states.get(ChargeControllerStates.Idle):
                    return ChargeControllerStates.Idle, True
                return ChargeControllerStates.Connected, True
            elif _state in self.model.charger_states.get(ChargeControllerStates.Done):
                return ChargeControllerStates.Done, False
            elif _state in self.model.charger_states.get(ChargeControllerStates.Idle):
                return ChargeControllerStates.Idle, True
            elif self.hub.sensors.power.killswitch.is_dead:  # todo: composition
                return ChargeControllerStates.Error, True
            elif all(
                [
                    _state
                    not in self.model.charger_states.get(ChargeControllerStates.Idle),
                    self.hub.charger_done,
                ]
            ):
                return ChargeControllerStates.Done, False
            elif all(
                [
                    datetime.now().hour in self.hub.non_hours,
                    not getattr(self.hub.hours.timer, "is_override", False),
                ]
            ):
                return ChargeControllerStates.Stop, True
            elif _state in self.model.charger_states.get(
                ChargeControllerStates.Connected
            ):
                return await self.async_get_status_connected(_state)
            elif _state in self.model.charger_states.get(
                ChargeControllerStates.Charging
            ):
                return await self.async_get_status_charging(), True
        except Exception as e:
            _LOGGER.debug(f"Error in async_get_status: {e}")
        _LOGGER.debug(f"async_get_status: {_state} returning Error. {str(_state)}")
        return ChargeControllerStates.Error, True

    async def async_get_status_outlet(self) -> Tuple[ChargeControllerStates, bool]:
        if not self.hub.enabled:
            return ChargeControllerStates.Connected, True
        elif self.hub.charger_done:
            return ChargeControllerStates.Done, True
        elif (
            datetime.now().hour in self.hub.non_hours
            and self.hub.hours.timer.is_override is False
        ):  # todo: composition
            return ChargeControllerStates.Stop, True
        elif (
            self.hub.chargertype.entities.powerswitch == "on"
            and self.hub.chargertype.entities.powermeter < 1
        ):  # todo: composition
            return await self.async_get_status_connected()
        else:
            return await self.async_get_status_charging(), True

    async def async_get_status_no_charger(self) -> Tuple[ChargeControllerStates, bool]:
        if (
            datetime.now().hour in self.hub.non_hours
            and not self.hub.hours.timer.is_override
        ):
            return ChargeControllerStates.Stop, True
        else:
            return ChargeControllerStates.Start, True

    async def async_is_done(self, charger_state) -> bool:
        if len(self.model.charger_states.get(ChargeControllerStates.Done)) > 0:
            if charger_state in self.model.charger_states.get(
                ChargeControllerStates.Done
            ):
                self.__debug_log(
                    f"'is_done' reported that charger is Done based on current charger state"
                )
                return await self.async_is_done_return(True)
        elif time.time() - self.model.latest_charger_start > DONETIMEOUT:
            self.__debug_log(
                f"'is_done' reported that charger is Done because of idle-charging for more than {DONETIMEOUT} seconds."
            )
            return await self.async_is_done_return(True)
        return False

    async def async_is_done_return(self, state: bool) -> bool:
        if state and self.hub.sensors.charger_done is False:
            await self.hub.observer.async_broadcast("update charger done", True)
        return state

    def __debug_log(self, message: str):
        if time.time() - self.model.latest_debuglog > DEBUGLOG_TIMEOUT:
            _LOGGER.debug(message)
            self.model.latest_debuglog = time.time()

    def _setup_observers(self) -> None:
        self.hub.observer.add(
            "update latest charger start", self.async_update_latest_charger_start
        )
        self.hub.observer.add(
            "update charger enabled", self.async_update_latest_charger_start
        )
        self.hub.observer.add("hub initialized", self._check_initialized)
        self.hub.observer.add("timer activated", self.async_set_status)

    @abstractmethod
    async def async_below_startthreshold(self) -> bool:
        pass

    @abstractmethod
    async def async_above_stopthreshold(self) -> bool:
        pass

    @property
    @abstractmethod
    def status_string(self) -> str:
        pass

    @abstractmethod
    async def async_get_status_charging(self) -> ChargeControllerStates:
        pass

    @abstractmethod
    async def async_get_status_connected(
        self, charger_state=None
    ) -> Tuple[ChargeControllerStates, bool]:
        pass
