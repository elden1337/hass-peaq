from peaqevcore.services.hourselection.initializers.price_aware_hours import \
    PriceAwareHours
from peaqevcore.services.hourselection.initializers.regular_hours import \
    RegularHours


class HourselectionFactory:
    @staticmethod
    async def async_create(hub):
        if hub.options.price.price_aware is False:
            return RegularHours(hub)
        else:
            return PriceAwareHours(hub)
