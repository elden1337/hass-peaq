import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class ServiceCalls:
    def __init__(self, hub):
        self.hub = hub

    async def call_enable_peaq(self):
        """peaqev.enable"""
        self.hub.observer.broadcast("update charger enabled", True)
        self.hub.observer.broadcast("update charger done", False)

    async def call_disable_peaq(self):
        """peaqev.disable"""
        self.hub.observer.broadcast("update charger enabled", False)
        self.hub.observer.broadcast("update charger done", False)

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
        dep_time = datetime.strptime(departure_time, '%y-%m-%d %H:%M')
        if schedule_starttime is not None:
            start_time = datetime.strptime(schedule_starttime, '%y-%m-%d %H:%M')
        else:
            start_time = datetime.now()
        _LOGGER.debug(f"scheduler params. charge: {charge_amount}, dep-time: {dep_time}, start_time: {start_time}")
        self.hub.scheduler.create_schedule(charge_amount, dep_time, start_time, override_settings)
        self.hub.scheduler.update()

    async def call_scheduler_cancel(self):
        self.hub.scheduler.cancel()
