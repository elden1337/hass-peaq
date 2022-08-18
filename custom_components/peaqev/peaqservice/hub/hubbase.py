import logging
from abc import abstractmethod

from homeassistant.core import (
    HomeAssistant,
    callback,
)
from peaqevcore.hub.hub_options import HubOptions

from custom_components.peaqev.peaqservice.charger.charger import Charger
from custom_components.peaqev.peaqservice.chargertypes.chargertypes import ChargerTypeData

_LOGGER = logging.getLogger(__name__)


class HubBase:
    """This is the shared baseclass for regular hub and hublite"""
    hub_id = 1337

    def __init__(
            self,
            hass: HomeAssistant,
            options: HubOptions,
            domain: str
    ):
        self.hass = hass
        self.hubname = domain.capitalize()
        self.domain = domain
        self.price_aware = options.price.price_aware
        self.peaqtype_is_lite = options.peaqev_lite

        self.chargertype = ChargerTypeData(
            hass,
            options.chargertype,
            options.chargerid
        )
        self.charger = Charger(
            self,
            hass,
            self.chargertype.charger.servicecalls
        )

    @abstractmethod
    def is_initialized(self) -> bool:
        pass

    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        try:
            if old_state is None or old_state.state != new_state.state:
                await self._update_sensor(entity_id, new_state.state)
        except Exception as e:
            msg = f"Unable to handle data: {entity_id} ({e})"
            _LOGGER.error(msg)

    @abstractmethod
    async def _update_sensor(self, entity, value):
        pass



