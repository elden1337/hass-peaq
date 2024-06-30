import logging
import time
from abc import abstractmethod
from typing import Tuple

from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.services.session.session import Session

from custom_components.peaqev.peaqservice.chargecontroller.charger.charger import \
    Charger
from custom_components.peaqev.peaqservice.chargecontroller.chargercontroller_model import \
    ChargeControllerModel
from custom_components.peaqev.peaqservice.chargecontroller.const import (
    DEBUGLOG_TIMEOUT, DONETIMEOUT)
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.const import LookupKeys
from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade
from custom_components.peaqev.peaqservice.util.extensionmethods import \
    log_once_per_minute

_LOGGER = logging.getLogger(__name__)


class IChargeController:
    """The interface for the charge controller"""

    def __init__(self, hub, charger_states, charger_type, observer: IObserver, state_machine: IHomeAssistantFacade):
        self.state_machine = state_machine
        self.hub = hub
        self.model = ChargeControllerModel(
            charger_type=charger_type, charger_states=charger_states
        )
        self.charger = Charger(controller=self, state_machine=state_machine, observer=observer) #todo: move out of here
        self.session = Session(self.charger) #todo: move out of here
        self.observer = observer
        self._setup_observers()

    async def async_setup(self):
        await self.session.async_setup()
        await self.charger.async_setup()

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

    @abstractmethod
    def _check_initialized(self) -> bool:
        pass

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
        if self.hub.options.price.price_aware and not self.hub.spotprice.is_initialized:  #todo: observer getter
            return False
        if self.hub.is_initialized and not self.model.is_initialized:  #todo: observer getter
            return self._check_initialized()
        return self.model.is_initialized

    async def async_update_latest_charger_start(self):
        if self.hub.enabled:
            self.model.latest_charger_start.update()

    def _do_initialize(self) -> bool:
        self.model.is_initialized = True
        log_once_per_minute('Chargecontroller is initialized and ready to work.', 'debug')
        self.model.latest_charger_start.update()
        return self.model.is_initialized

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
                    _LOGGER.debug(f'Error in async_set_status1: {e}')
                    ret = ChargeControllerStates.Error
                if update_timer is True:
                    await self.async_update_latest_charger_start()
                await self.async_set_status_type(ret)
            else:
                _LOGGER.debug('chargecontroller is not init')
        except Exception as e:
            _LOGGER.debug(f'Error in async_set_status2: {e}')

    @abstractmethod
    async def _aux_check_running_charger_mismatch(self, status_type: ChargeControllerStates) -> None:
        pass

    async def async_set_status_type(self, status_type: ChargeControllerStates) -> None:
        try:
            if isinstance(status_type, ChargeControllerStates):
                if status_type != self.status_type:
                    await self.async_check_broadcasting(
                        old_state=self.status_type, new_state=status_type
                    )
                    self.model.status_type = status_type
                    if self.model.charger_type is not ChargerType.NoCharger: #todo: strategy should handle this
                        await self.observer.async_broadcast(ObserverTypes.ProcessCharger)
                await self._aux_check_running_charger_mismatch(status_type)
        except Exception as e:
            _LOGGER.debug(f'Error in async_set_status_type: {e}')

    async def async_check_broadcasting(
        self, old_state: ChargeControllerStates, new_state: ChargeControllerStates
    ) -> None:
        _LOGGER.debug(f'async_check_broadcasting: {old_state} -> {new_state}')
        match new_state:
            case ChargeControllerStates.Idle:
                await self.observer.async_broadcast(ObserverTypes.CarDisconnected)
                await self.session.async_reset(
                    getattr(
                        self.hub.sensors.locale.data.query_model,
                        'charged_peak',
                        0,
                    )
                )
                if self.hub.charger_done: #todo: this should not be a prop of hub but only here. change so that it works via observer setter
                    await self.observer.async_broadcast(
                        ObserverTypes.UpdateChargerDone, False
                    )

            case ChargeControllerStates.Done:
                await self.observer.async_broadcast(ObserverTypes.UpdateChargerDone, True)
            case ChargeControllerStates.Charging | ChargeControllerStates.Start | ChargeControllerStates.Stop | ChargeControllerStates.Connected:
                if old_state in [
                    ChargeControllerStates.Idle,
                    ChargeControllerStates.Disabled,
                ]:
                    await self.observer.async_broadcast(ObserverTypes.CarConnected)
                if old_state == ChargeControllerStates.Stop:
                    _LOGGER.debug('Car is allowed to start charging now.')
            case _:
                pass

    async def async_get_status(self) -> Tuple[ChargeControllerStates, bool]:
        state = await self.hub.async_request_sensor_data(LookupKeys.CHARGEROBJECT_VALUE) #todo: observer getter

        if state not in self.model.flattened_chargerstates():
            _LOGGER.error(f'Chargerobject_value is not in charger_states. Returning Error-state. {str(state)}')
            return ChargeControllerStates.Error, True

        if self.hub.sensors.power.killswitch.is_caution: #todo: shouldn't be here at all. if killswitch is caution it should be handled by the strategy
            _LOGGER.warning('Killswitch is caution, it may disengage soon.')
        extended_errors = []
        try:
            if not self.hub.enabled:
                if state in self.model.charger_states[ChargeControllerStates.Idle]:
                    return ChargeControllerStates.Idle, True
                return ChargeControllerStates.Connected, True

            if state in self.model.charger_states[ChargeControllerStates.Done]:
                return ChargeControllerStates.Done, False

            if state in self.model.charger_states[ChargeControllerStates.Idle]:
                return ChargeControllerStates.Idle, True

            if self.hub.sensors.power.killswitch.is_dead:
                _LOGGER.debug('Killswitch is dead. Returning Error-state.') #todo: this should be handled by observer from killswitch.
                await self.observer.async_broadcast(ObserverTypes.KillswitchDead)
                return ChargeControllerStates.Error, True

            if not state in self.model.charger_states[ChargeControllerStates.Idle] and self.hub.charger_done: #todo: see l152
                return ChargeControllerStates.Done, False

            if self.hub.now_is_non_hour() and not getattr(self.hub.hours.timer, 'is_override', False): #todo: obsever getter
                return ChargeControllerStates.Stop, True

            if state in self.model.charger_states[ChargeControllerStates.Connected]:
                try:
                    return await self.async_get_status_connected(state)
                except Exception as e:
                    extended_errors.append(f'Error in async_get_status_connected: {e}')

            if state in self.model.charger_states[ChargeControllerStates.Charging]:
                try:
                    return await self.async_get_status_charging(), True
                except Exception as e:
                    extended_errors.append(f'Error in async_get_status_charging: {e}')

        except Exception as e:
            _LOGGER.exception(f'Error in async_get_status: {e}. Extended errors {extended_errors}')
            _LOGGER.debug(f'state (chargerobj value): {state}')

        _LOGGER.error(f'async_get_status: {state} returning Error. {str(state)}')
        return ChargeControllerStates.Error, True


    async def async_get_status_outlet(self) -> Tuple[ChargeControllerStates, bool]:
        if not self.hub.enabled:
            return ChargeControllerStates.Connected, True
        elif self.hub.charger_done: #todo: see l152
            return ChargeControllerStates.Done, True
        elif (
            self.hub.now_is_non_hour()  #todo: observer getter
            and self.hub.hours.timer.is_override is False #todo: observer getter
        ):
            return ChargeControllerStates.Stop, True
        elif (
            self.hub.chargertype.entities.powerswitch == 'on' #todo: observer getter
            and self.hub.chargertype.entities.powermeter < 1 #todo: observer getter
        ):
            return await self.async_get_status_connected()
        else:
            return await self.async_get_status_charging(), True

    async def async_get_status_no_charger(self) -> Tuple[ChargeControllerStates, bool]:
        if (
            self.hub.now_is_non_hour() #todo: observer getter
            and not self.hub.hours.timer.is_override #todo: observer getter
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
        elif self.model.latest_charger_start.is_timeout():
            self.__debug_log(
                f"'is_done' reported that charger is Done because of idle-charging for more than {DONETIMEOUT} seconds."
            )
            return await self.async_is_done_return(True)
        return False

    async def async_is_done_return(self, state: bool) -> bool:
        if state and self.hub.sensors.charger_done is False:  #todo: see l152
            await self.observer.async_broadcast(ObserverTypes.UpdateChargerDone, True)
        return state

    def __debug_log(self, message: str): #todo: move to extensions or shared
        if time.time() - self.model.latest_debuglog > DEBUGLOG_TIMEOUT:
            _LOGGER.debug(message)
            self.model.latest_debuglog = time.time()

    def _setup_observers(self) -> None:
        self.observer.add(
            ObserverTypes.UpdateLatestChargerStart, self.async_update_latest_charger_start
        )
        self.observer.add(
            ObserverTypes.UpdateChargerEnabled, self.async_update_latest_charger_start
        )
        self.observer.add(ObserverTypes.HubInitialized, self._check_initialized)
        self.observer.add(ObserverTypes.TimerActivated, self.async_set_status)
        self.observer.add(ObserverTypes.AuxStopChanged, self.async_set_status)
        self.observer.add(ObserverTypes.ProcessChargeController, self.async_set_status)
