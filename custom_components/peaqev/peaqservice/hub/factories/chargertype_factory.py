import logging

from homeassistant.core import HomeAssistant
from peaqevcore.services.chargertype.chargertype_base import ChargerBase

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.chargertypes.types.chargeamps import \
    ChargeAmps
from custom_components.peaqev.peaqservice.chargertypes.types.easee import Easee
from custom_components.peaqev.peaqservice.chargertypes.types.garowallbox import \
    GaroWallbox
from custom_components.peaqev.peaqservice.chargertypes.types.no_charger import \
    NoCharger
from custom_components.peaqev.peaqservice.chargertypes.types.outlet import \
    SmartOutlet
from custom_components.peaqev.peaqservice.chargertypes.types.zaptec import \
    Zaptec
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions

_LOGGER = logging.getLogger(__name__)


class ChargerTypeFactory:
    @staticmethod
    async def async_get_class(input_type: str):
        types_dict = {
            ChargerType.ChargeAmps: ChargeAmps,
            ChargerType.Easee: Easee,
            ChargerType.Outlet: SmartOutlet,
            ChargerType.GaroWallbox: GaroWallbox,
            ChargerType.Zaptec: Zaptec,
            ChargerType.NoCharger: NoCharger,
        }

        try:
            return types_dict.get(ChargerType(input_type))
        except Exception as e:
            _LOGGER.debug(f"Caught exception while parsing charger-type: {e}")
            raise ValueError

    @staticmethod
    async def async_create(hass: HomeAssistant, options: HubOptions) -> ChargerBase:
        input_type = options.charger.chargertype
        try:
            charger = await ChargerTypeFactory.async_get_class(input_type)
            # charger.validatecharger()
            ret = charger(hass=hass, huboptions=options, chargertype=ChargerType(input_type))
            await ret.async_setup()
            _LOGGER.info(f"Set up charger-class for chargertype {input_type} is done.")
            return ret
        except Exception as e:
            _LOGGER.debug(f"Exception. Did not manage to set up charge-class for {input_type}: {e}")
            raise Exception
