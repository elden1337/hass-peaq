from peaqevcore.models.const import CURRENTS_THREEPHASE_1_32, CURRENTS_THREEPHASE_1_16

FUSE_3_16 = "3phase 16A"
FUSE_3_20 = "3phase 20A"
FUSE_3_25 = "3phase 25A"
FUSE_3_35 = "3phase 35A"
FUSE_3_50 = "3phase 50A"
FUSE_3_63 = "3phase 63A"
DEFAULT = "Not set"

FUSES_LIST = [
    FUSE_3_16,
    FUSE_3_20,
    FUSE_3_25,
    FUSE_3_35,
    FUSE_3_50,
    FUSE_3_63,
    DEFAULT
]

FUSES_DICT = {
    FUSE_3_16: 11000,
    FUSE_3_20: 14000,
    FUSE_3_25: 17000,
    FUSE_3_35: 24000,
    FUSE_3_50: 35000,
    FUSE_3_63: 44000
}

MAINS_THRESHOLD = 0.9


class PowerOrchestrator:
    def __init(self, hub):
        self._hub = hub
        self._fuse_max = hub.options.fuse_max
        self._current_amps: int = 0
        self._current_car_power: int = 0
        self._current_total_power: int = 0
        self._threephase_amps: dict = self._set_allowed_threephase_amps()

    @property
    def threephase_amps(self) -> dict:
        return self._threephase_amps

    @property
    def alive(self) -> bool:
        """if returns false no charging can be conducted"""
        return False

    def allow_adjustment(self, new_amps: int) -> bool:
        """this method returns true if the desired adjustment 'new_amps' is not breaching threshold"""
        return False

    def _set_allowed_threephase_amps(self) -> dict:
        """only allow amps 16-32 threephase if user has set this value high enough"""
        if self._fuse_max > 0:
            return {k: v for (k, v) in CURRENTS_THREEPHASE_1_32.items() if k < self._fuse_max}
        return CURRENTS_THREEPHASE_1_16

    """
    1 if trying to raise amps and they would hit mains-treshold, dont raise
    2 if approaching mains-threshold on current amps. Lower if possible, else turn off
    3 only allow amps 16-32 threephase if user has set this value high enough
    """
