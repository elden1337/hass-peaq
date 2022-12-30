import logging

from homeassistant.core import HomeAssistant
from peaqevcore.hub.hub_options import HubOptions

from custom_components.peaqev.peaqservice.chargertypes.types.chargeamps import ChargeAmps
from custom_components.peaqev.peaqservice.chargertypes.types.easee import Easee
from custom_components.peaqev.peaqservice.chargertypes.types.garowallbox import GaroWallbox
from custom_components.peaqev.peaqservice.chargertypes.types.outlet import SmartOutlet
from custom_components.peaqev.peaqservice.chargertypes.types.zaptec import Zaptec
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGERTYPE_EASEE, CHARGERTYPE_CHARGEAMPS, CHARGERTYPE_OUTLET, CHARGERTYPE_GAROWALLBOX, CHARGERTYPE_ZAPTEC
)

_LOGGER = logging.getLogger(__name__)

CHARGERTYPE_DICT = {
            CHARGERTYPE_CHARGEAMPS: ChargeAmps,
            CHARGERTYPE_EASEE: Easee,
            CHARGERTYPE_OUTLET: SmartOutlet,
            CHARGERTYPE_GAROWALLBOX: GaroWallbox,
            CHARGERTYPE_ZAPTEC: Zaptec
        }


class ChargerTypeData:
    def __init__(self, hass: HomeAssistant, input_type, options: HubOptions):
        self._charger = None
        self._type = input_type
        self._hass = hass
        try:
            self._charger = CHARGERTYPE_DICT[input_type](hass=self._hass, huboptions=options)
            self._charger.validatecharger()
        except Exception as e:
            raise Exception

    @property
    def type(self) -> str:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def charger(self):
        """charger returns the set charger with all its properties of states, servicecalls etc."""
        return self._charger
