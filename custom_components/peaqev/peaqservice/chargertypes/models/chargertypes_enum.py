import logging
from enum import Enum

_LOGGER = logging.getLogger(__name__)


class ChargerType(Enum):
    ChargeAmps = "Chargeamps"
    Easee = "Easee"
    GaroWallbox = "Garo Wallbox"
    Outlet = "Smart outdoor plug"
    Zaptec = "Zaptec"
    NoCharger = "None"
    Unknown = "Unknown"
    WallBox = "Wallbox"


CHARGERTYPES = [
    ChargerType.ChargeAmps.value,
    ChargerType.Easee.value,
    ChargerType.Outlet.value,
    # Charger_type.GaroWallbox.value,
    # Charger_type.WallBox.value,
    ChargerType.Zaptec.value,
    ChargerType.NoCharger.value,
]
