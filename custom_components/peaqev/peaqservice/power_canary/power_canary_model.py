from dataclasses import dataclass, field

from peaqevcore.models.const import CURRENTS_THREEPHASE_1_32, CURRENTS_THREEPHASE_1_16, CURRENTS_ONEPHASE_1_16, \
    CURRENTS_ONEPHASE_1_32
from peaqevcore.models.fuses import Fuses


@dataclass
class PowerCanaryModel:
    warning_threshold: float
    cutoff_threshold: float
    fuse: Fuses
    allow_amp_adjustment: bool
    threephase_amps: dict = field(init=False)
    onephase_amps: dict = field(init=False)
    fuse_max: int = field(init=False)

    def __post_init__(self):
        self.fuse_max = self.FUSES_DICT[self.fuse] if self.fuse is not None else 0
        self.threephase_amps = self._set_allowed_amps(CURRENTS_THREEPHASE_1_32, CURRENTS_THREEPHASE_1_16)
        self.onephase_amps = self._set_allowed_amps(CURRENTS_ONEPHASE_1_32, CURRENTS_ONEPHASE_1_16)

    def _set_allowed_amps(self, amps_dict, default_amps) -> dict:
        """only allow amps if user has set this value high enough"""
        if self.fuse_max > 0:
            return {k: v for (k, v) in default_amps.items() if k < self.fuse_max}
        return default_amps

    @property
    def is_valid(self) -> bool:
        if self.fuse_max == 0:
            return True
        else:
            return self.fuse_max == self.FUSES_DICT[self.fuse]

    FUSES_DICT = {
        Fuses.FUSE_3_16: 11000,
        Fuses.FUSE_3_20: 14000,
        Fuses.FUSE_3_25: 17000,
        Fuses.FUSE_3_35: 24000,
        Fuses.FUSE_3_50: 35000,
        Fuses.FUSE_3_63: 44000,
        Fuses.DEFAULT:   0
    }