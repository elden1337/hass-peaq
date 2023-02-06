import logging
from enum import Enum

from custom_components.peaqev.peaqservice.chargertypes.types.chargeamps import ChargeAmps
from custom_components.peaqev.peaqservice.chargertypes.types.easee import Easee
from custom_components.peaqev.peaqservice.chargertypes.types.garowallbox import GaroWallbox
from custom_components.peaqev.peaqservice.chargertypes.types.outlet import SmartOutlet
from custom_components.peaqev.peaqservice.chargertypes.types.zaptec import Zaptec

_LOGGER = logging.getLogger(__name__)

class Charger_type(Enum):
    ChargeAmps = "Chargeamps"
    Easee = "Easee"
    GaroWallbox = "Garo Wallbox"
    Outlet = "Smart outdoor plug"
    Zaptec = "Zaptec"

    @staticmethod
    def get_class(input_type: str):
        types_dict = {
            Charger_type.ChargeAmps:  ChargeAmps,
            Charger_type.Easee:       Easee,
            Charger_type.Outlet:      SmartOutlet,
            Charger_type.GaroWallbox: GaroWallbox,
            Charger_type.Zaptec:      Zaptec
        }

        try:
            return types_dict[Charger_type(input_type)]
        except Exception as e:
            _LOGGER.debug(f"Caught exception while parsing charger-type: {e}")
            raise ValueError

CHARGERTYPES = [
    Charger_type.ChargeAmps.value,
    Charger_type.Easee.value,
    Charger_type.Outlet.value,
    #Charger_type.GaroWallbox.value,
    Charger_type.Zaptec.value
    ]
