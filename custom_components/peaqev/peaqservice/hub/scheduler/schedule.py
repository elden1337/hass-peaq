from datetime import datetime

from peaqevcore.models.chargerstates import CHARGERSTATES
from peaqevcore.services.scheduler.scheduler import Scheduler as core_scheduler


class Scheduler:
    def __init__(self, hub, options):
        self._hub = hub
        self.scheduler = core_scheduler(options)
        self.schedule_created = False

    def create_schedule(self, charge_amount: float, departure_time: datetime, schedule_starttime: datetime, override_settings: bool = False):
        if not self.scheduler_active:
            self.scheduler.create(charge_amount, departure_time, schedule_starttime, override_settings)
        self.schedule_created = True

    def update(self):
        self.scheduler.update(
            avg24=self._hub.powersensormovingaverage24.value,
            peak=self._hub.current_peak_dynamic,
            charged_amount=self._hub.charger.session.session_energy,
            prices=self._hub.hours.prices,
            prices_tomorrow=self._hub.hours.prices_tomorrow
        )
        self.check_states()

    def cancel(self):
        self.scheduler.cancel()
        self.schedule_created = False

    def check_states(self):
        if not self.scheduler_active and self.schedule_created:
            self.cancel()
        elif self._hub.chargecontroller.status is CHARGERSTATES.Done.name:
            self.cancel()

    @property
    def non_hours(self) -> list:
        return self.scheduler.model.non_hours

    @property
    def caution_hours(self) -> dict:
        """dynamic caution hours"""
        return self.scheduler.model.caution_hours

    @property
    def scheduler_active(self) -> bool:
        return self.scheduler.scheduler_active
