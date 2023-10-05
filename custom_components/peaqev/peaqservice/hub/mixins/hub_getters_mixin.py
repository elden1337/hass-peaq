import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

class HubGettersMixin:

    def now_is_non_hour(self) -> bool:
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        return now in self.non_hours

    def now_is_caution_hour(self) -> bool:
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        return now in self.dynamic_caution_hours.keys()

    async def async_free_charge(self) -> bool:
        """Returns true if free charge is enabled, which means that peaks are currently not tracked"""
        try:
            return await self.sensors.locale.data.async_free_charge()
        except Exception as e:
            _LOGGER.debug(f"Unable to get free charge. Exception: {e}")
            return False

    async def async_predictedpercentageofpeak(self):
        ret = await self.prediction.async_predicted_percentage_of_peak(
            predicted_energy=await self.async_get_predicted_energy(),
            peak=self.sensors.current_peak.value,
        )
        self.model.peak_breached = ret > 100
        return ret

    async def async_threshold_start(self):
        return await self.threshold.async_start(
            is_caution_hour=await self.async_is_caution_hour(),
            is_quarterly=await self.sensors.locale.data.async_is_quarterly(),
        )

    async def async_threshold_stop(self):
        return await self.threshold.async_stop(
            is_caution_hour=await self.async_is_caution_hour(),
            is_quarterly=await self.sensors.locale.data.async_is_quarterly(),
        )

    async def async_get_predicted_energy(self) -> float:
        ret = await self.prediction.async_predicted_energy(
            power_avg=self.sensors.powersensormovingaverage.value,
            total_hourly_energy=self.sensors.totalhourlyenergy.value,
            is_quarterly=await self.sensors.locale.data.async_is_quarterly(),
        )
        return ret