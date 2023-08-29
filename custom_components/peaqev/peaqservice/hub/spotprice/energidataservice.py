import asyncio
import logging

from custom_components.peaqev.peaqservice.hub.spotprice.const import ENERGIDATASERVICE, ENERGIDATASERVICE_SENSOR
from custom_components.peaqev.peaqservice.hub.spotprice.ispotprice import ISpotPrice
from custom_components.peaqev.peaqservice.hub.spotprice.models.spotprice_dto import EnergiDataServiceDTO

_LOGGER = logging.getLogger(__name__)


class EnergiDataServiceUpdater(ISpotPrice):
    def __init__(self, hub, test:bool = False, is_active: bool = True):
        super().__init__(hub=hub, source=ENERGIDATASERVICE, test=test, is_active=is_active)

    async def async_set_dto(self, ret, initial: bool = False) -> None:
        _result = EnergiDataServiceDTO()
        await _result.set_model(ret)
        if await self.async_update_set_prices(_result):
            if initial:
                await self.hub.async_update_prices(
                    [self.model.prices, self.model.prices_tomorrow]
                )
                await self.hub.observer.async_broadcast("spotprice initialized")
            else:
                await self.hub.observer.async_broadcast(
                    "prices changed",
                    [self.model.prices, self.model.prices_tomorrow],
                )
            self._is_initialized = True

    def setup(self):
        try:
            sensor = self.state_machine.states.get(ENERGIDATASERVICE_SENSOR)
            if not sensor.state:
                self.hub.options.price.price_aware = False  # todo: composition
                _LOGGER.error(
                    f"There were no Spotprice-entities. Cannot continue. with price-awareness: {e}"
                )
            else:
                self.model.entity = ENERGIDATASERVICE_SENSOR
                _LOGGER.debug(
                    f"EnergiDataService has been set up and is ready to be used with {self.model.entity}"
                )
                asyncio.run_coroutine_threadsafe(
                    self.async_update_spotprice(),
                    self.state_machine.loop,
                )
        except Exception as e:
            self.hub.options.price.price_aware = False  # todo: composition
            _LOGGER.error(
                f"I was unable to get a Spotprice-entity. Cannot continue. with price-awareness: {e}"
            )