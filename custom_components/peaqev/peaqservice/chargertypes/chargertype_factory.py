import logging

from homeassistant.core import HomeAssistant
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.services.chargertype.chargertype_base import ChargerBase

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.chargertypes.types.chargeamps import ChargeAmps
from custom_components.peaqev.peaqservice.chargertypes.types.easee import Easee
from custom_components.peaqev.peaqservice.chargertypes.types.garowallbox import GaroWallbox
from custom_components.peaqev.peaqservice.chargertypes.types.outlet import SmartOutlet
from custom_components.peaqev.peaqservice.chargertypes.types.zaptec import Zaptec
from custom_components.peaqev.peaqservice.chargertypes.types.no_charger import NoCharger

_LOGGER = logging.getLogger(__name__)


class ChargerTypeFactory:

    @staticmethod
    def get_class(input_type: str):
        types_dict = {
            ChargerType.ChargeAmps:  ChargeAmps,
            ChargerType.Easee:       Easee,
            ChargerType.Outlet:      SmartOutlet,
            ChargerType.GaroWallbox: GaroWallbox,
            ChargerType.Zaptec:      Zaptec, 
            ChargerType.NoCharger: NoCharger
        }

        try:
            return types_dict[ChargerType(input_type)]
        except Exception as e:
            _LOGGER.debug(f"Caught exception while parsing charger-type: {e}")
            raise ValueError

    @staticmethod
    def create(hass: HomeAssistant, input_type, options: HubOptions) -> ChargerBase:
        try:
            if not ChargerType(input_type) == ChargerType.NoCharger:
                charger = ChargerTypeFactory.get_class(input_type)(hass=hass, huboptions=options, chargertype=ChargerType(input_type))
                _LOGGER.debug(f"Managed to set up charger-class for chargertype {input_type}")
                charger.validatecharger()
                return charger
            return None
        except Exception as e:
            _LOGGER.debug(f"Exception. Did not manage to set up charge-class for {input_type}: {e}")
            raise Exception
