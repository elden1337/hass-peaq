import logging
from abc import abstractmethod
from datetime import date

from custom_components.peaqev.peaqservice.hub.spotprice.dynamic_top_price import \
    DynamicTopPrice
from custom_components.peaqev.peaqservice.hub.spotprice.models.spotprice_dto import \
    ISpotPriceDTO
from custom_components.peaqev.peaqservice.hub.spotprice.models.spotprice_model import \
    SpotPriceModel
from custom_components.peaqev.peaqservice.hub.spotprice.spotprice_average_mixin import \
    SpotPriceAverageMixin

_LOGGER = logging.getLogger(__name__)


class ISpotPrice(SpotPriceAverageMixin):
    def __init__(self, hub, source: str, test:bool = False, is_active: bool = True):
        _LOGGER.debug(f"Initializing Spotprice for {source}.")
        self.hub = hub
        self.model = SpotPriceModel(source=source)
        self._is_initialized: bool = False
        self._dynamic_top_price = DynamicTopPrice()
        if not test:
            self.state_machine = hub.state_machine
            if is_active:
                self.setup()

    @property
    def entity(self) -> str:
        return getattr(self.model, "entity", "")

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    @property
    def currency(self) -> str:
        return self.model.currency

    @property
    def state(self) -> float:
        return self.model.state

    @state.setter
    def state(self, val) -> None:
        if self.model.state != val:
            self.model.state = val

    @property
    def use_cent(self) -> bool:
        return self.model.use_cent

    @property
    def source(self) -> str:
        return self.model.source

    @property
    def average_month(self) -> float:
        return self.model.average_month

    @property
    def average_weekly(self) -> float:
        return self.model.average_weekly

    @property
    def average_30(self) -> float:
        return self.model.average_30

    @property
    def average_data(self) -> dict[date, float]:
        return self.model.average_data

    @abstractmethod
    async def async_set_dto(self, ret, initial: bool) -> None:
        pass

    @abstractmethod
    def setup(self):
        pass

    async def async_update_spotprice(self, initial: bool = False) -> None:
        if self.entity is not None:
            ret = self.state_machine.states.get(self.entity)
            if ret is not None:
                await self.async_set_dto(ret, initial)
            else:
                _LOGGER.debug(
                    f"Could not get spot-prices. Entity: {self.entity}. Retrying..."
                )
    async def async_update_set_prices(self, result: ISpotPriceDTO) -> bool:
        ret = False
        today = await self.model.fix_dst(result.today)
        if self.model.prices != today:
            self.model.prices = today
            ret = True
        if result.tomorrow_valid:
            tomorrow = await self.model.fix_dst(result.tomorrow)
            if self.model.prices_tomorrow != tomorrow:
                self.model.prices_tomorrow = tomorrow
                ret = True
        else:
            if self.model.prices_tomorrow:
                self.model.prices_tomorrow = []
                ret = True
        await self.async_update_average([3, 7, 30])
        self.model.currency = result.currency
        self.model.use_cent = result.price_in_cent
        self.state = result.state
        await self.async_update_average_day(result.average)
        await self.async_update_average_month()
        await self.async_update_dynamic_max_price()
        return ret

    async def async_update_dynamic_max_price(self):
        if len(self.model.average_data) > 3:
            _dynamic_max_price = await self._dynamic_top_price.async_get_max(
                list(self.model.average_data.values())
            )
            if self.model.dynamic_top_price != _dynamic_max_price[0]:
                self.model.dynamic_top_price_type = _dynamic_max_price[1].value
                self.model.dynamic_top_price = _dynamic_max_price[0]
                #_LOGGER.debug(_dynamic_max_price)
                await self.hub.observer.async_broadcast(
                    "dynamic max price changed", _dynamic_max_price[0]
                )








