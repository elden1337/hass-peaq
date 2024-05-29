from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from peaqevcore.common.models.observer_types import ObserverTypes

from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub import HomeAssistantHub

_LOGGER = logging.getLogger(__name__)

"""
Todo: inject options
Todo: inject hours
"""


class MaxMinController:
    def __init__(self, hub: HomeAssistantHub, observer: IObserver, state_machine: IHomeAssistantFacade, max_charge: int):
        self.hub: HomeAssistantHub = hub
        self._max_charge = max_charge
        self.observer = observer
        self.state_machine = state_machine
        self.active: bool = hub.options.price.price_aware
        self.is_on: bool = False
        self._override_max_charge = None
        self._original_total_charge = 0
        self._max_min_limiter: float = 0
        self.override_max_charge: bool = False
        if not hub.options.peaqev_lite:
            self.observer.add(ObserverTypes.CarDisconnected, self.async_null_max_charge)
            self.observer.add(
                ObserverTypes.UpdateChargerDone, self.async_null_max_charge_done
            )
            self.observer.add(ObserverTypes.UpdateChargerEnabled, self.async_null_max_charge)
            self.observer.add(ObserverTypes.MaxMinLimiterChanged, self.async_update_maxmin_core)
            self.observer.add(ObserverTypes.ResetMaxMinChargeSensor, self.async_try_reset_max_charge_sensor)

    @property
    def max_charge(self) -> int:
        if self.active:
            if self._override_max_charge is not None:
                """overridden by frontend"""
                self.is_on = True
                return self._override_max_charge
            if self._max_charge > 0:
                """set in config flow"""
                self.is_on = True
                return self._max_charge
        return self._original_total_charge

    @property
    def remaining_charge(self) -> float:
        if not self.active:
            return 0
        return self.max_charge - getattr(
            self.hub.chargecontroller.session, 'session_energy', 0
        )  # todo: get this via observer?

    @property
    def max_min_limiter(self) -> float:
        return self._max_min_limiter

    @max_min_limiter.setter
    def max_min_limiter(self, val: float):
        self._max_min_limiter = val
        self.observer.broadcast(ObserverTypes.MaxMinLimiterChanged)

    async def async_override_max_charge(self, max_charge: int):
        """Overrides the max-charge with the input from frontend"""
        if self.active:
            self._override_max_charge = max_charge
            _LOGGER.debug(f'Max charge overridden to {max_charge}kWh. Updating max_min with {self.max_charge}')
            await self.async_update_maxmin_core()

    async def async_update_maxmin_core(self) -> None:
        await self.hub.hours.async_update_max_min(
            max_charge=self.max_charge,
            limiter=self.max_min_limiter,
            session_energy=self.hub.chargecontroller.session.session_energy,
            car_connected=self.hub.chargecontroller.connected
        )  #todo: make observertype of this instead?

    async def async_servicecall_override_charge_amount(self, amount: int):
        await self.async_override_max_charge(amount)
        await self.async_update_sensor(amount)

    async def async_servicecall_reset_charge_amount(self):
        self._override_max_charge = None
        await self.async_reset_max_charge_sensor()

    async def async_null_max_charge_done(self, val):
        if val and self.active:
            await self.async_null_max_charge()

    async def async_null_max_charge(self, val=None):
        """Resets the max-charge to the static value, listens to charger done and charger disconnected"""
        if val is None:
            self._override_max_charge = None
        elif val is False:
            self._override_max_charge = None
        if self._override_max_charge is None:
            await self.async_reset_max_charge_sensor()

    async def async_try_reset_max_charge_sensor(self) -> None:
        if not self.override_max_charge:
            await self.async_reset_max_charge_sensor()

    async def async_reset_max_charge_sensor(self) -> None:
        if self.active:
            try:
                state = self.state_machine.get_state('number.peaqev_max_charge')
                if state is not None:
                    if (
                            int(float(state.state)) == int(float(self.max_charge))
                            or self.max_charge == 0
                    ):
                        return
                    else:
                        await self.async_update_sensor(self.max_charge)
                        _LOGGER.debug(
                            f'Resetting max charge to static value {int(float(self.max_charge))} because of {state.state}'
                        )
            except Exception as e:
                _LOGGER.error(
                    f'Encountered problem when trying to reset max charge to normal: {e}'
                )
                return

    async def async_update_sensor(self, val):
        if self.active:
            _LOGGER.debug(f'Updating input number-sensor for maxmin with {val}')
            await self.state_machine.async_call_service(
                'number',
                'set_value',
                {
                    'entity_id': 'number.peaqev_max_charge',
                    'value':     int(val),
                },
            )
