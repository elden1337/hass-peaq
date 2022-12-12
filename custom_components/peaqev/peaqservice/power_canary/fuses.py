import logging
from enum import Enum

_LOGGER = logging.getLogger(__name__)


class Fuses(Enum):
    FUSE_3_16 = "3phase 16A"
    FUSE_3_20 = "3phase 20A"
    FUSE_3_25 = "3phase 25A"
    FUSE_3_35 = "3phase 35A"
    FUSE_3_50 = "3phase 50A"
    FUSE_3_63 = "3phase 63A"
    DEFAULT = "Not set"

    def parse_from_config(fusetype: str):
        try:
            for f in Fuses:
                if fusetype == f.value:
                    return f
        except Exception as e:
            print("Unable to parse fuse-type, invalid value: {e}")
            return Fuses.DEFAULT
