from __future__ import annotations
from typing import TYPE_CHECKING, Tuple
import logging

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import (
        ChargerType,
    )
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_helpers import (
    async_defer_start,
)
from custom_components.peaqev.peaqservice.chargecontroller.const import (
    INITIALIZING,
    WAITING_FOR_POWER,
)
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import (
    IChargeController,
)

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
        if not self.hub.power.power_canary.alive:
            return ChargeControllerStates.Stop
        if all(
            [
                await self.async_above_stopthreshold(),
                self.hub.sensors.totalhourlyenergy.value > 0,
                not await self.hub.async_free_charge(),
            ]
        ):
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
                return ChargeControllerStates.Done, False
            else:
                if all(
                    [
                        any(
                            [
                                (
                                    await self.async_below_startthreshold()
                                    and self.hub.sensors.totalhourlyenergy.value != 0
                                ),
                                await self.hub.async_free_charge(),
                            ]
                        ),
                        not await async_defer_start(self.hub.hours.non_hours),
                    ]
                ):
                    return ChargeControllerStates.Start, False
                else:
                    return ChargeControllerStates.Stop, True
        except Exception as e:
            _LOGGER.error(f"async_get_status_connected for: {e}")
            return ChargeControllerStates.Error, True
