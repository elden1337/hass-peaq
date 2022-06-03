from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.chargertypes.types.chargeamps import ChargeAmps
from custom_components.peaqev.peaqservice.chargertypes.types.easee import Easee
from custom_components.peaqev.peaqservice.chargertypes.types.garowallbox import GaroWallbox
from custom_components.peaqev.peaqservice.chargertypes.types.ocpp import OCPP
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGERTYPE_EASEE, CHARGERTYPE_CHARGEAMPS, CHARGERTYPE_GAROWALLBOX, CHARGERTYPE_OCPP
)


class ChargerTypeData:
    def __init__(self, hass: HomeAssistant, input_type, chargerid):
        self._charger = None
        self._type = input_type
        self._hass = hass

        CHARGERYPEDICT = {
            CHARGERTYPE_CHARGEAMPS: ChargeAmps(self._hass, chargerid),
            CHARGERTYPE_EASEE: Easee(self._hass, chargerid),
            CHARGERTYPE_GAROWALLBOX: GaroWallbox(self._hass, chargerid),
            CHARGERTYPE_OCPP: OCPP(self._hass, chargerid)
        }

        self._charger = CHARGERYPEDICT[input_type]
        self._charger.validatecharger()

    @property
    def type(self) -> str:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def charger(self):
        """charger returns the set charger with all its properties of states, servicecalls etc."""
        return self._charger
