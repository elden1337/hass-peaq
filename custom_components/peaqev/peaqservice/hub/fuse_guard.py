# from peaqevcore.models.fuses import Fuses
from enum import Enum

from peaqevcore.models.const import CURRENTS_THREEPHASE_1_32, CURRENTS_THREEPHASE_1_16


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


FUSES_DICT = {
    Fuses.FUSE_3_16: 11000,
    Fuses.FUSE_3_20: 14000,
    Fuses.FUSE_3_25: 17000,
    Fuses.FUSE_3_35: 24000,
    Fuses.FUSE_3_50: 35000,
    Fuses.FUSE_3_63: 44000
}

FUSES_LIST = [f.value for f in Fuses]

MAINS_THRESHOLD = 0.9
MAINS_REDLINE = 0.75


class FuseGuard:
    def __init(self, hub):
        self._hub = hub
        self._fuse = Fuses.parse_from_config(hub.options.fuse)
        self._fuse_max = FUSES_DICT[self._fuse]
        # self._current_amps: int = 0
        # self._current_car_power: int = 0
        self._threephase_amps: dict = self._set_allowed_threephase_amps()
        self._enabled: bool = False
        self._allow_amp_adjustment: bool = self._hub.chargertype.charger.servicecalls.options.allowupdatecurrent
        self._validate()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def active(self) -> bool:
        return self._active

    @property
    def alive(self) -> bool:
        """if returns false no charging can be conducted"""
        if self._enabled is False:
            return True
        return self._hub.sensors.power.total.value < self._fuse_max * MAINS_THRESHOLD

    @property
    def current_percentage(self) -> float:
        return self._hub.sensors.power.total.value / self._fuse_max

    @property
    def state_string(self) -> str:
        if not self.enabled:
            return "Disabled"
        if not self.alive:
            return f"Critical. Lower consumption! {round(self.current_percentage * 100, 0)}%"
        if self.active:
            if self.current_percentage >= MAINS_REDLINE:
                return f"Warning! {round(self.current_percentage * 100, 0)}%"
            return f"Ok. {round(self.current_percentage * 100, 0)}%"

    @property
    def threephase_amps(self) -> dict:
        return self._threephase_amps

    def allow_adjustment(self, new_amps: int) -> bool:
        """this method returns true if the desired adjustment 'new_amps' is not breaching threshold"""
        if not self._allow_amp_adjustment:
            return False
        return False

    def _set_allowed_threephase_amps(self) -> dict:
        """only allow amps 16-32 threephase if user has set this value high enough"""
        if self._fuse_max > 0:
            return {k: v for (k, v) in CURRENTS_THREEPHASE_1_32.items() if k < self._fuse_max}
        return CURRENTS_THREEPHASE_1_16

    def _validate(self):
        if self._fuse_max == 0:
            return
        assert self._fuse_max == FUSES_DICT[self._fuse]
        self._enabled = True
        self._active = True

    """
    1 if trying to raise amps and they would hit mains-treshold, dont raise
    2 if approaching mains-threshold on current amps. Lower if possible, else turn off
    3 only allow amps 16-32 threephase if user has set this value high enough
    """
