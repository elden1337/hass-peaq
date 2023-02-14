import logging

from homeassistant.core import HomeAssistant
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.services.chargertype.chargertype_base import ChargerBase
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType


_LOGGER = logging.getLogger(__name__)

class NoCharger(ChargerBase):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, chargertype):
        self._type = chargertype

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return "No charger"