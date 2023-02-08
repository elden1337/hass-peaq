import logging

from homeassistant.core import HomeAssistant
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.services.chargertype.chargertype_base import ChargerBase

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import Charger_type

_LOGGER = logging.getLogger(__name__)


class ChargerTypeData:
    # def __init__(self, hass: HomeAssistant, input_type, options: HubOptions):
    #     self._charger = None
    #     self._type = Charger_type(input_type)
    #     self._hass = hass
    #     try:
    #         self._charger = Charger_type.get_class(input_type)(hass=self._hass, huboptions=options)
    #         _LOGGER.debug(f"Managed to set up charger-class for chargertype {input_type}")
    #         self._charger.validatecharger()
    #     except Exception as e:
    #         _LOGGER.debug(f"Exception. Did not manage to set up charge-class for {input_type}: {e}")
    #         raise Exception
    #
    # @property
    # def type(self) -> Charger_type:
    #     """type returns the implemented chargertype."""
    #     return self._type
    #
    # @property
    # def charger(self):
    #     """charger returns the set charger with all its properties of states, servicecalls etc."""
    #     return self._charger

    @staticmethod
    def create(hass: HomeAssistant, input_type, options: HubOptions) -> ChargerBase:
        try:
            charger = Charger_type.get_class(input_type)(hass=hass, huboptions=options, chargertype=Charger_type(input_type))
            _LOGGER.debug(f"Managed to set up charger-class for chargertype {input_type}")
            charger.validatecharger()
            return charger
        except Exception as e:
            _LOGGER.debug(f"Exception. Did not manage to set up charge-class for {input_type}: {e}")
            raise Exception
