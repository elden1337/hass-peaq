from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

from datetime import datetime

from peaqevcore.services.savings.savings_service import SavingsService
from peaqevcore.services.savings.savings_status import SavingsStatus


class SavingsController:
    def __init__(self, hub: HomeAssistantHub):
        self.hub = hub
        self.service = SavingsService()
        self.hub.observer.add("car connected", self.async_enter)

    @property
    def savings_peak(self) -> float:
        return self.service.savings_peak

    @property
    def savings_trade(self) -> float:
        return self.service.savings_trade

    @property
    def savings_total(self) -> float:
        return self.service.savings_total

    @property
    def status(self) -> SavingsStatus:
        return self.service.status

    async def async_export_data(self) -> dict:
        return await self.service.async_export_data()

    async def async_enter(self):
        #if car is being  connected to charger
        if self.status is SavingsStatus.Off:
            await self.service.async_start_listen(datetime.now())

    async def async_exit(self):
        #if car is being disconnected from charger
        if self.status is SavingsStatus.On:
            await self.service.async_stop_listen()

    async def async_add_consumption(self, hourly_sum:float):
        await self.service.async_add_to_registered_consumption(hourly_sum, datetime.now().date, datetime.now().hour)

    async def async_add_peak(self, current_peak):
        await self.service.async_add_to_peaks(current_peak, datetime.now().date, datetime.now().hour)



