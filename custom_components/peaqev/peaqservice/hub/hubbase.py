import logging
from abc import abstractmethod

from homeassistant.core import (
    HomeAssistant,
    callback,
)

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.hourselection import (PriceAwareHours, RegularHours)
from custom_components.peaqev.peaqservice.hub.hubmember.hubmember import HubMember
from custom_components.peaqev.peaqservice.util.constants import CHARGERENABLED, CHARGERDONE

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
        self.peaqtype_is_lite = config_inputs["peaqtype_is_lite"]

        if self.price_aware is True:
            self.hours = PriceAwareHours(
                hass=self.hass,
                absolute_top_price=config_inputs["absolute_top_price"],
                cautionhour_type=config_inputs["cautionhour_type"],
                min_price=config_inputs["min_price"],
                hub=self,
                allow_top_up=config_inputs["allow_top_up"]
            )
        else:
            self.hours = RegularHours(
                non_hours=config_inputs["nonhours"],
                caution_hours=config_inputs["cautionhours"]
            )

        self.charger_enabled = HubMember(
            data_type=bool,
            listenerentity=f"binary_sensor.{domain}_{ex.nametoid(CHARGERENABLED)}",
            initval=False
        )
        self.charger_done = HubMember(
            data_type=bool,
            listenerentity=f"binary_sensor.{domain}_{ex.nametoid(CHARGERDONE)}",
            initval=False
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

    async def call_enable_peaq(self):
        """peaqev.enable"""
        self.charger_enabled.value = True
        self.charger_done.value = False

    async def call_disable_peaq(self):
        """peaqev.disable"""
        self.charger_enabled.value = False
        self.charger_done.value = False
