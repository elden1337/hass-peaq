from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Tuple

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.observer.models.observer_types import \
    ObserverTypes

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_helpers import \
    defer_start
from custom_components.peaqev.peaqservice.chargecontroller.const import (
    INITIALIZING, WAITING_FOR_POWER)
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import \
    IChargeController

_LOGGER = logging.getLogger(__name__)


class ChargeController(IChargeController):
    def __init__(
        self, hub: HomeAssistantHub, charger_states: dict, charger_type: ChargerType
    ):
        super().__init__(hub, charger_states, charger_type)

    @property
    def status_string(self) -> str:
        if not self.is_initialized:
            return INITIALIZING
        if not self._check_initialized():
            return WAITING_FOR_POWER
        return self.status_type.name

    def _check_initialized(self) -> bool:
        if self.model.is_initialized:
            return True
        _state = self.hub.get_power_sensor_from_hass()
        if _state is not None:
            if isinstance(_state, (float, int)):
                if _state > 0:
                    return self._do_initialize()
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
        except Exception as e:
            _LOGGER.debug(
                f"async_get_status_connected for: {e}. charger-state: {charger_state}"
            )
            return ChargeControllerStates.Error, True

    async def _should_start_charging(self) -> bool:
        return all([
            any([
                await self.async_below_startthreshold() and self.hub.sensors.totalhourlyenergy.value != 0,
                await self.hub.async_free_charge()
            ]),
            any([not defer_start(self.hub.hours.non_hours), getattr(self.hub.hours.timer, "is_override", True)]),
            not self.hub.events.aux_stop
        ])
