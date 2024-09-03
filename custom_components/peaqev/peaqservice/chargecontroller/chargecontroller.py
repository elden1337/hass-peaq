from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING, Tuple

from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.common.wait_timer import WaitTimer
from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_helpers import \
    defer_start
from custom_components.peaqev.peaqservice.chargecontroller.const import (
    INITIALIZING, WAITING_FOR_POWER)
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import \
    IChargeController
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.util.extensionmethods import \
    log_once_per_minute

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

_LOGGER = logging.getLogger(__name__)


class ChargeController(IChargeController):
    def __init__(
            self, hub: HomeAssistantHub, charger_states: dict, charger_type: ChargerType
    ):
        self._aux_running_grace_timer = WaitTimer(timeout=300, init_now=True)
        self.latest_init_check: float = time.time()
        super().__init__(hub, charger_states, charger_type)

    @property
    def status_string(self) -> str:
        if not self.is_initialized:
            self._check_initialized()
            return INITIALIZING
        if not self._check_initialized():
            return WAITING_FOR_POWER
        return self.status_type.name

    def _check_initialized(self) -> bool:
        if self.model.is_initialized:
            return True
        if time.time() - self.latest_init_check < 10:
            return False
        self.latest_init_check = time.time()
        _state = self.hub.state_machine.states.get(self.hub.options.powersensor)
        _LOGGER.debug(f'Checking if initialized {self.hub.options.powersensor}. State: {_state.state or None}')
        if _state is not None:
            try:
                float_state = float(_state.state)
                if isinstance(float_state, (float, int)):
                    if float_state > 0:
                        return self._do_initialize()
            except Exception as e:
                log_once_per_minute(f'Could not convert state to float for sensor ({self.hub.options.powersensor}). Exception: {e}', 'error')
        return False

    async def async_below_startthreshold(self) -> bool:
        energy, peak = await self.async_get_energy_and_peak()
        threshold_start = await self.hub.threshold.async_start() / 100
        return (energy * 1000) < ((peak * 1000) * threshold_start)

    async def async_above_stopthreshold(self) -> bool:
        energy, peak = await self.async_get_energy_and_peak()
        threshold_stop = await self.hub.threshold.async_stop() / 100
        return (energy * 1000) > ((peak * 1000) * threshold_stop)

    async def async_get_energy_and_peak(self) -> Tuple[float, float]:
        predicted_energy = await self.hub.async_get_predicted_energy()
        current_peak = self.hub.current_peak_dynamic
        return predicted_energy, current_peak

    async def async_get_status_charging(self) -> ChargeControllerStates:
        if any([not self.hub.power.power_canary.alive, self.hub.events.aux_stop,
                all(
                    [
                        await self.async_above_stopthreshold(),
                        self.hub.sensors.totalhourlyenergy.value > 0,
                        not await self.hub.async_free_charge(),
                        datetime.now().minute < 59 #attempt to avoid unnecessary quick stops at end of hour.
                    ]
                )]):
            return ChargeControllerStates.Stop
        return ChargeControllerStates.Start

    async def async_get_status_connected(
            self, charger_state=None
    ) -> Tuple[ChargeControllerStates, bool]:
        try:
            if not self.hub.enabled:
                return ChargeControllerStates.Connected, True
            if (
                    charger_state is not None
                    and self.hub.sensors.carpowersensor.value < 1
                    and await self.async_is_done(charger_state)
            ):
                await self.hub.observer.async_broadcast(ObserverTypes.CarDone)
                return ChargeControllerStates.Done, False
            if await self._should_start_charging():
                return ChargeControllerStates.Start, False
            return ChargeControllerStates.Stop, True
        except TypeError as e:
            _LOGGER.error(
                'TypeError in async_get_status_connected for: %s. charger-state: %s', e, charger_state
            )
            return ChargeControllerStates.Error, True
        except ValueError as e:
            _LOGGER.error(
                'ValueError in async_get_status_connected for: %s. charger-state: %s', e, charger_state
            )
            return ChargeControllerStates.Error, True
        # Add more specific exceptions as needed
        except Exception as e:
            _LOGGER.error(
                'Unexpected error in async_get_status_connected for: %s. charger-state: %s', e, charger_state
            )
            return ChargeControllerStates.Error, True

    async def _aux_check_running_charger_mismatch(self, status_type: ChargeControllerStates) -> None:
        if self._aux_running_grace_timer.is_timeout():
            if status_type == ChargeControllerStates.Charging:
                _LOGGER.warning('Charger seems to be running without Peaqev controlling it. Attempting aux stop. If you wish to charge without Peaqev you need to disable it on the switch.')
            await self.hub.observer.async_broadcast(ObserverTypes.KillswitchDead)
            self._aux_running_grace_timer.reset()
        elif status_type in [
            ChargeControllerStates.Idle,
            ChargeControllerStates.Done,
            ChargeControllerStates.Error,
            ChargeControllerStates.Connected
        ] and self.hub.sensors.carpowersensor.value > 0:
            return
        self._aux_running_grace_timer.update()

    async def _should_start_charging(self) -> bool:
        aux_stop = self.hub.events.aux_stop
        dont_defer_nonhour = not defer_start(self.hub.non_hours)
        timer_is_override = getattr(self.hub.hours.timer, 'is_override', True)
        is_free_charge = await self.hub.async_free_charge()
        is_below_treshold = await self.async_below_startthreshold()
        energy_has_value = self.hub.sensors.totalhourlyenergy.value != 0

        return all([
            any([
                is_below_treshold and energy_has_value,
                is_free_charge
            ]),
            any([dont_defer_nonhour, timer_is_override]),
            not aux_stop
        ])
