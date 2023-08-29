import logging

from custom_components.peaqev.peaqservice.hub.spotprice.const import *
from custom_components.peaqev.peaqservice.hub.spotprice.energidataservice import EnergiDataServiceUpdater
from custom_components.peaqev.peaqservice.hub.spotprice.ispotprice import ISpotPrice
from custom_components.peaqev.peaqservice.hub.spotprice.nordpool import NordPoolUpdater

_LOGGER = logging.getLogger(__name__)


class SpotPriceFactory:

    sources = {
        NORDPOOL: NordPoolUpdater,
        ENERGIDATASERVICE: EnergiDataServiceUpdater
    }

    @staticmethod
    def create(hub, test:bool = False, is_active: bool = False) -> ISpotPrice:
        if test:
            return NordPoolUpdater(hub, test)
        source = SpotPriceFactory.test_connections(hub.state_machine)
        return SpotPriceFactory.sources[source](hub, test, is_active)

    @staticmethod
    def test_connections(hass) -> str:
        sensor = hass.states.get(ENERGIDATASERVICE_SENSOR)       
        if sensor:
            _LOGGER.debug("Found sensor %s", sensor)
            return ENERGIDATASERVICE
        else:
            _LOGGER.debug("No sensor %s", sensor)
            return NORDPOOL
                

    