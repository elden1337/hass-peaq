import logging
from enum import Enum

_LOGGER = logging.getLogger(__name__)


class ChargeAmpsTypes(Enum):
    Halo = "Halo"
    Aura = "Aura"
    Dawn = "Dawn"
    Unknown = "Unknown"

    @staticmethod
    def get_type(type_string: str):
        types = {
            "halo": ChargeAmpsTypes.Halo,
            "aura": ChargeAmpsTypes.Aura,
            "dawn": ChargeAmpsTypes.Dawn
        }
        try:
            return types[type_string.lower()]
        except:
            _LOGGER.warning("Unable to identify Chargeamps type.")
            return ChargeAmpsTypes.Unknown
