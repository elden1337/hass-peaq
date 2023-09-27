import logging
from datetime import date, datetime
from statistics import mean

from custom_components.peaqev.peaqservice.hub.observer.models.observer_types import \
    ObserverTypes
from custom_components.peaqev.peaqservice.hub.spotprice.const import \
    AVERAGE_MAX_LEN

_LOGGER = logging.getLogger(__name__)


class SpotPriceAverageMixin:
    async def async_update_average_month(self) -> None:
        _new = self._get_average(datetime.now().day)
        if (
            len(self.model.average_data) >= int(datetime.now().day)
            and self.model.average_month != _new
        ):
            self.model.average_month = _new
            if self.model.average_month is not None:
                await self.hub.observer.async_broadcast(
                    ObserverTypes.MonthlyAveragePriceChanged, self.model.average_month
                )

    async def async_update_average(self, length: list[int]) -> None:
        averages_dict = {
            3: "average_three_days",
            7: "average_weekly",
            30: "average_30",
        }
        for l in length:
            _new = self._get_average(l)
            if len(self.model.average_data) >= l and getattr(self.model, averages_dict[l]) != _new:
                setattr(self.model, averages_dict[l], _new)
                _LOGGER.debug(f"average {str(l)} updated to {_new}")
        await self.async_update_adjusted_average()

    async def async_update_adjusted_average(self) -> None:
        adj_avg: float|None = None
        if len(self.model.average_data) >= 7:
            adj_avg = max(self.model.average_weekly, self.model.average_three_days)
        elif len(self.model.average_data) >= 3:
            adj_avg = self.model.average_three_days
        if self.model.adjusted_average != adj_avg and adj_avg is not None:
            self.model.adjusted_average = adj_avg
            await self.hub.observer.async_broadcast(
                ObserverTypes.AdjustedAveragePriceChanged, adj_avg
            )

    async def async_update_average_day(self, average) -> None:
        if average != self.model.daily_average:
            self.model.daily_average = average
            await self.async_add_average_data(average)
            await self.hub.observer.async_broadcast(
                ObserverTypes.DailyAveragePriceChanged, average
            )

    async def async_import_average_data(self, incoming: list|dict):
        if len(incoming):
            self.model.create_date_dict(incoming)
        await self.async_cap_average_data_length()
        await self.async_update_spotprice()

    async def async_add_average_data(self, new_val):
        if isinstance(new_val, float):
            rounded = round(new_val, 3)
            if datetime.now().date not in self.model.average_data.keys():
                self.model.average_data[date.today()] = rounded
            await self.async_cap_average_data_length()

    async def async_cap_average_data_length(self):
        while len(self.model.average_data) > AVERAGE_MAX_LEN:
            min_key = min(self.model.average_data.keys())
            del self.model.average_data[min_key]

    def _get_average(self, days: int) -> float:
        try:
            if len(self.model.average_data) > days:
                avg_values = list(self.model.average_data.values())
                ret = avg_values[-days:]
            elif len(self.model.average_data) == 0:
                return 0.0
            else:
                ret = list(self.model.average_data.values())
            return round(mean(ret), 2)
        except Exception as e:
            _LOGGER.debug(
                f"Could not calculate average. indata: {list(self.model.average_data.values())}, error: {e}"
            )
