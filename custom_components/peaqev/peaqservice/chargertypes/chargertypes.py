from homeassistant.core import HomeAssistant

import custom_components.peaqev.peaqservice.util.constants as constants
from custom_components.peaqev.peaqservice.chargertypes.types.chargeamps import ChargeAmps
from custom_components.peaqev.peaqservice.chargertypes.types.easee import Easee


class ChargerTypeData:
    def __init__(self, hass: HomeAssistant, input_type, chargerid):
        self._charger = None
        self._type = input_type
        self._hass = hass

        if input_type == constants.CHARGERTYPE_CHARGEAMPS:
            self._charger = ChargeAmps(self._hass, chargerid)
        elif input_type == constants.CHARGERTYPE_EASEE:
            self._charger = Easee(self._hass, chargerid)

        self._charger.validatecharger()

    @property
    def type(self) -> str:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def charger(self):
        """charger returns the set charger with all its properties of states, servicecalls etc."""
        return self._charger

