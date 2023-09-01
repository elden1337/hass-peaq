from datetime import datetime

class HubGettersMixin:
    def now_is_non_hour(self) -> bool:
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        return now in self.non_hours

    async def async_free_charge(self) -> bool:
        try:
            return await self.sensors.locale.data.async_free_charge()
        except Exception as e:
            return False

    async def async_predictedpercentageofpeak(self):
        return await self.prediction.async_predicted_percentage_of_peak(
            predicted_energy=await self.async_get_predicted_energy(),
            peak=self.sensors.current_peak.value,
        )

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

    async def async_is_caution_hour(self) -> bool:
        if self.options.price.price_aware:
            return False
        return str(datetime.now().hour) in [str(h) for h in self.hours.caution_hours]

    async def async_get_predicted_energy(self) -> float:
        ret = await self.prediction.async_predicted_energy(
            power_avg=self.sensors.powersensormovingaverage.value,
            total_hourly_energy=self.sensors.totalhourlyenergy.value,
            is_quarterly=await self.sensors.locale.data.async_is_quarterly(),
        )
        return ret