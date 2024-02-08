from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from peaqevcore.common.models.observer_types import ObserverTypes

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import (
        IChargeController,
    )

from peaqevcore.services.savings.savings_service import SavingsService
from peaqevcore.services.savings.savings_status import SavingsStatus

_LOGGER = logging.getLogger(__name__)


class SavingsController:
    def __init__(self, chargecontroller: IChargeController):
        self.controller = chargecontroller
        self._prices: list = []
        self.service = SavingsService(
            peak_price=self.controller.hub.sensors.locale.data.price.value
        )  # todo: must be dynamic to adhere to tiered prices.
        if self.controller.hub.sensors.locale.data.price.is_active:
            self.controller.hub.observer.add(ObserverTypes.CarConnected, self.async_enter)
            self.controller.hub.observer.add(ObserverTypes.CarDisconnected, self.async_exit)
            self.controller.hub.observer.add(ObserverTypes.UpdateChargerDone, self.async_exit)
            self.controller.hub.observer.add(ObserverTypes.PricesChanged, self.async_update_prices)
            self._enabled = True
        else:
            self._enabled = False

    @property
    def is_on(self) -> bool:
        return self.status == SavingsStatus.Collecting

    @property
    def status(self) -> SavingsStatus:
        return self.service.status

    @property
    def enabled(self) -> bool:
        if self._enabled:
            return self.service.enabled
        return self._enabled

    @property
    def savings_peak(self) -> float:
        return self.service.savings_peak

    @property
    def savings_trade(self) -> float:
        return self.service.savings_trade

    @property
    def savings_total(self) -> float:
        return self.service.savings_total

    async def async_export_data(self) -> dict:
        return await self.service.async_export_data()

    async def async_import_data(self, data: dict) -> None:
        await self.service.async_import_data(data)

    async def async_enter(self):
        #_LOGGER.debug("SavingsController: async_enter")
        # if car is being  connected to charger
        if self.status is SavingsStatus.Off:
            await self.service.async_start_listen()
            prices = await self.controller.hub.async_request_sensor_data("prices")
            await self.service.async_add_prices(prices)

    async def async_exit(self, val=None):
        # if car is being disconnected from charger or done
        do = True
        if val is not None:
            if not val:
                do = False
        if do:
            if self.status is SavingsStatus.Collecting:
                try:
                    await self.service.async_register_charge_session(
                        charge_session=self.controller.session.session_data,
                        original_peak=self.controller.session.original_peak,
                    )
                    await self.service.async_stop_listen()
                except Exception:
                    #_LOGGER.warning(f"Problem with savingsservice stop listening: {e}")
                    return

    async def async_update_prices(self, prices) -> None:
        if self.is_on:
            if prices[0] != self._prices:
                self._prices = prices[0]
                await self.service.async_add_prices(prices=prices[0])

    async def async_add_consumption(self, hourly_sum: float):
        if self.is_on:
            await self.service.async_add_to_consumption(hourly_sum)
            # await self.service.async_add_to_peaks(hourly_sum)
