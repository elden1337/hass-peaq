import logging
from abc import abstractmethod

from homeassistant.core import (
    HomeAssistant,
    callback,
)

import custom_components.peaqev.peaqservice.util.constants as constants
import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.hourselection import (PriceAwareHours, RegularHours)
from custom_components.peaqev.peaqservice.hub.hubdata.hubmember import HubMember

_LOGGER = logging.getLogger(__name__)


class HubBase:
    """This is the shared baseclass for regular hub and hublite"""
    hub_id = 1337

    def __init__(
            self,
            hass: HomeAssistant,
            config_inputs: dict,
            domain: str
    ):
        self.hass = hass
        self.hubname = domain.capitalize()
        self.domain = domain
        self.price_aware = config_inputs["priceaware"]

        if self.price_aware is True:
            self.hours = PriceAwareHours(
                hass=self.hass,
                absolute_top_price=config_inputs["absolute_top_price"],
                non_hours=config_inputs["nonhours"],
                caution_hours=config_inputs["cautionhours"],
                cautionhour_type=config_inputs["cautionhour_type"]
            )
        else:
            self.hours = RegularHours(
                non_hours=config_inputs["nonhours"],
                caution_hours=config_inputs["cautionhours"]
            )

        self.charger_enabled = HubMember(
            data_type=bool,
            listenerentity=f"binary_sensor.{domain}_{ex.nametoid(constants.CHARGERENABLED)}",
            initval=False
        )
        self.charger_done = HubMember(
            data_type=bool,
            listenerentity=f"binary_sensor.{domain}_{ex.nametoid(constants.CHARGERDONE)}",
            initval=False
        )



    async def is_initialized(self) -> bool:
        return True

    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        try:
            if old_state is None or old_state.state != new_state.state:
                await self._updatesensor(entity_id, new_state.state)
        except Exception as e:
            msg = f"Unable to handle data: {entity_id} {e}"
            _LOGGER.error(msg)
            pass

    @abstractmethod
    async def _updatesensor(self, entity, value):
        pass

    async def call_enable_peaq(self):
        """peaqev.enable"""
        self.charger_enabled.value = True
        self.charger_done.value = False

    async def call_disable_peaq(self):
        """peaqev.disable"""
        self.charger_enabled.value = False
        self.charger_done.value = False
