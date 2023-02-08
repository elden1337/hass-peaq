import logging
from enum import Enum

# from custom_components.peaqev.peaqservice.chargertypes.types.chargeamps import ChargeAmps
# from custom_components.peaqev.peaqservice.chargertypes.types.easee import Easee
# from custom_components.peaqev.peaqservice.chargertypes.types.garowallbox import GaroWallbox
# from custom_components.peaqev.peaqservice.chargertypes.types.outlet import SmartOutlet
# from custom_components.peaqev.peaqservice.chargertypes.types.zaptec import Zaptec

_LOGGER = logging.getLogger(__name__)


class ChargerType(Enum):
    ChargeAmps = "Chargeamps"
    Easee = "Easee"
    GaroWallbox = "Garo Wallbox"
    Outlet = "Smart outdoor plug"
    Zaptec = "Zaptec"

    # @staticmethod
    # def get_class(input_type: str):
    #     types_dict = {
    #         ChargerType.ChargeAmps:  ChargeAmps,
    #         ChargerType.Easee:       Easee,
    #         ChargerType.Outlet:      SmartOutlet,
    #         ChargerType.GaroWallbox: GaroWallbox,
    #         ChargerType.Zaptec:      Zaptec
    #     }
    #
    #     try:
    #         return types_dict[ChargerType(input_type)]
    #     except Exception as e:
    #         _LOGGER.debug(f"Caught exception while parsing charger-type: {e}")
    #         raise ValueError


CHARGERTYPES = [
    ChargerType.ChargeAmps.value,
    ChargerType.Easee.value,
    ChargerType.Outlet.value,
    # Charger_type.GaroWallbox.value,
    ChargerType.Zaptec.value
]
