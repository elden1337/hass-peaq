import custom_components.peaqev.peaqservice.constants as constants
from homeassistant.core import HomeAssistant
import logging

from custom_components.peaqev.peaqservice.chargertypes.types.chargeamps import ChargeAmps
from custom_components.peaqev.peaqservice.chargertypes.types.easee import Easee


class ChargerTypeData():
    def __init__(self, hass: HomeAssistant, input, chargerid):
        self._charger = None
        self._type = input
        self._hass = hass

        if input == constants.CHARGERTYPE_CHARGEAMPS:
            self._charger = ChargeAmps(self._hass, chargerid)
        elif input == constants.CHARGERTYPE_EASEE:
            self._charger = Easee(self._hass, chargerid)

        self._charger.validatecharger()

    """type returns the implemented chargertype."""
    @property
    def type(self) -> str:
        return self._type

    """charger returns the set charger with all its properties of states, servicecalls etc."""
    @property
    def charger(self):
        return self._charger






