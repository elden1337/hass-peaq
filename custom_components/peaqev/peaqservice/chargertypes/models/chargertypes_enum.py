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
    Keba = "Keba"


CHARGERTYPES = [
    ChargerType.ChargeAmps.value,
    ChargerType.Easee.value,
    ChargerType.GaroWallbox.value,
    ChargerType.Keba.value,
    ChargerType.Outlet.value,
    ChargerType.WallBox.value,
    ChargerType.Zaptec.value,
    ChargerType.NoCharger.value,
]
