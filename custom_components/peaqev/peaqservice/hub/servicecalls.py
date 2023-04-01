import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class ServiceCalls:
    def __init__(self, hub):
        self.hub = hub

    async def call_enable_peaq(self):
        """peaqev.enable"""        
        await self.hub.observer.async_broadcast("update charger enabled", True)
        await self.hub.observer.async_broadcast("update charger done", False)

    async def call_disable_peaq(self):
        """peaqev.disable"""
        await self.hub.observer.async_broadcast("update charger enabled", False)
        await self.hub.observer.async_broadcast("update charger done", False)

    async def call_override_nonhours(self, hours: int = 1):
        """peaqev.override_nonhours"""
        self.hub.timer.update(hours)

    async def call_schedule_needed_charge(
            self,
            charge_amount: float,
            departure_time: str,
            schedule_starttime: str = None,
            override_settings: bool = False
    ):
        dep_time = None
        start_time = None
        try:
            dep_time = datetime.strptime(departure_time, '%Y-%m-%d %H:%M')
        except ValueError:
            _LOGGER.error(f"Could not parse departure time: {departure_time}")
        if schedule_starttime is not None:
            try:
                start_time = datetime.strptime(schedule_starttime, '%Y-%m-%d %H:%M')
            except ValueError:
                _LOGGER.error(f"Could not parse schedule start time: {schedule_starttime}")
        else:
            start_time = datetime.now()
        _LOGGER.debug(f"scheduler params. charge: {charge_amount}, dep-time: {dep_time}, start_time: {start_time}")
        await self.hub.scheduler.async_create_schedule(charge_amount, dep_time, start_time, override_settings)
        await self.hub.scheduler.async_update()

    async def call_scheduler_cancel(self):
        await self.hub.scheduler.async_cancel()
