from __future__ import annotations

from typing import TYPE_CHECKING

from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.services.scheduler.update_scheduler_dto import \
    UpdateSchedulerDTO

from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class ServiceCalls:
    def __init__(self, hub: HomeAssistantHub, observer: IObserver):
        self.hub = hub
        self.observer = observer

    async def async_call_enable_peaq(self):
        """peaqev.enable"""
        await self.observer.async_broadcast(ObserverTypes.UpdateChargerEnabled, True)
        await self.observer.async_broadcast(ObserverTypes.UpdateChargerDone, False)

    async def async_call_disable_peaq(self):
        """peaqev.disable"""
        await self.observer.async_broadcast(ObserverTypes.UpdateChargerEnabled, False)
        await self.observer.async_broadcast(ObserverTypes.UpdateChargerDone, False)

    async def async_call_override_nonhours(self, hours: int = 1):
        """peaqev.override_nonhours"""
        if self.hub.options.price.price_aware:
            await self.hub.hours.timer.async_update(hours) #todo: make observercall
            await self.observer.async_broadcast(ObserverTypes.TimerActivated)

    async def async_call_schedule_needed_charge(
        self,
        charge_amount: float,
        departure_time: str,
        schedule_starttime: str = None,
        override_settings: bool = False,
    ):
        if not self.hub.options.price.price_aware:
            return

        dep_time = None
        start_time = None
        try:
            dep_time = datetime.strptime(departure_time, '%Y-%m-%d %H:%M')
        except ValueError:
            _LOGGER.error(f'Could not parse departure time: {departure_time}')
        if schedule_starttime is not None:
            try:
                start_time = datetime.strptime(schedule_starttime, '%Y-%m-%d %H:%M')
            except ValueError:
                _LOGGER.error(f'Could not parse schedule start time: {schedule_starttime}')
        else:
            start_time = datetime.now()
        _LOGGER.debug(
            f'scheduler params. charge: {charge_amount}, dep-time: {dep_time}, start_time: {start_time}'
        )
        if self.hub.hours.scheduler.scheduler_active:
            _LOGGER.debug('Scheduler already active, cancelling before adding new.')
            await self.hub.hours.scheduler.async_cancel_facade()
        await self.hub.hours.scheduler.async_create_schedule(
            charge_amount, dep_time, start_time, override_settings
        )
        dto = UpdateSchedulerDTO(
            moving_avg24=self.hub.sensors.powersensormovingaverage24.value,
            peak=self.hub.current_peak_dynamic,
            charged_amount=self.hub.chargecontroller.session.session_energy,
            prices=self.hub.hours.prices,
            prices_tomorrow=self.hub.hours.prices_tomorrow,
            chargecontroller_state = self.hub.chargecontroller.status_type
        )
        await self.hub.hours.scheduler.async_update_facade(dto) #todo: make observercall, send that to a hub function that takes the above params to decouple
        await self.observer.async_broadcast(ObserverTypes.SchedulerCreated)

    async def async_call_scheduler_cancel(self):
        if self.hub.hours.price_aware:
            await self.hub.hours.scheduler.async_cancel_facade() #todo: make observercall
            await self.observer.async_broadcast(ObserverTypes.SchedulerCancelled)
