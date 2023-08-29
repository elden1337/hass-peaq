import asyncio
import logging

import homeassistant.helpers.template as template

from custom_components.peaqev.peaqservice.hub.spotprice.const import NORDPOOL
from custom_components.peaqev.peaqservice.hub.spotprice.ispotprice import ISpotPrice
from custom_components.peaqev.peaqservice.hub.spotprice.models.spotprice_dto import NordpoolDTO

_LOGGER = logging.getLogger(__name__)


class NordPoolUpdater(ISpotPrice):
    def __init__(self, hub, test:bool = False, is_active: bool = True):
        super().__init__(hub=hub, source=NORDPOOL, test=test, is_active=is_active)

    async def async_set_dto(self, ret, initial: bool = False) -> None:
        _result = NordpoolDTO()
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
            entities = template.integration_entities(self.state_machine, NORDPOOL)
            _LOGGER.debug(f"Found {list(entities)} Spotprice entities for {self.model.source}.")
            if len(list(entities)) < 1:
                self.hub.options.price.price_aware = False  # todo: composition
                _LOGGER.error(
                    f"There were no Spotprice-entities. Cannot continue. with price-awareness: {e}"
                )
            if len(list(entities)) == 1:
                self._setup_set_entity(entities[0])
            else:
                _found: bool = False
                for e in list(entities):
                    if self._test_sensor(e):
                        _found = True
                        self._setup_set_entity(e)
                        break
                if not _found:
                    self.hub.options.price.price_aware = False  # todo: composition
                    _LOGGER.error(f"more than one Spotprice entity found. Cannot continue with price-awareness.")
        except Exception as e:
            self.hub.options.price.price_aware = False  # todo: composition
            _LOGGER.error(
                f"I was unable to get a Spotprice-entity. Cannot continue with price-awareness: {e}"
            )

    def _setup_set_entity(self, entity: str) -> None:
        self.model.entity = entity
        _LOGGER.debug(
            f"Nordpool has been set up and is ready to be used with {self.entity}"
        )
        asyncio.run_coroutine_threadsafe(
            self.async_update_spotprice(),
            self.state_machine.loop,
        )

    def _test_sensor(self, sensor: str) -> bool:
        """
        Testing whether the sensor has a set value for additional_costs_current_hour.
        This is the only way we can differ when there are multiple sensors present.
        """
        _LOGGER.debug(f"testing sensor {sensor}")
        state = self.state_machine.states.get(sensor)
        if state:
            _LOGGER.debug(f"got state")
            attr = state.attributes.get("additional_costs_current_hour", 0)
            _LOGGER.debug(f"testing attribute {attr}")
            if attr != 0:
                return True
        return False
