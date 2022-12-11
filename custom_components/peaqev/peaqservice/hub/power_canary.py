# from peaqevcore.models.fuses import Fuses
from enum import Enum

from peaqevcore.models.const import CURRENTS_THREEPHASE_1_32, CURRENTS_THREEPHASE_1_16, CURRENTS_ONEPHASE_1_16, \
    CURRENTS_ONEPHASE_1_32


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

CUTOFF_THRESHOLD = 0.9
WARNING_THRESHOLD = 0.75


class PowerCanary:
    warning_threshold: float = WARNING_THRESHOLD
    cutoff_threshold: float = CUTOFF_THRESHOLD

    def __init__(self, hub):
        self._enabled: bool = False
        self._active: bool = False
        self._hub = hub
        self._fuse = Fuses.parse_from_config(hub.options.fuse_type)
        self._fuse_max = FUSES_DICT[self._fuse] if self._fuse is not None else 0
        self._threephase_amps: dict = self._set_allowed_amps(CURRENTS_THREEPHASE_1_32, CURRENTS_THREEPHASE_1_16)
        self._onephase_amps: dict = self._set_allowed_amps(CURRENTS_ONEPHASE_1_32, CURRENTS_ONEPHASE_1_16)
        self._allow_amp_adjustment: bool = self._hub.chargertype.charger.servicecalls.options.allowupdatecurrent
        self._validate()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def fuse(self) -> str:
        return self._fuse.value

    @property
    def active(self) -> bool:
        return self._active

    @property
    def alive(self) -> bool:
        """if returns false no charging can be conducted"""
        if self._enabled is False:
            return True
        return self._hub.sensors.power.total.value < self._fuse_max * CUTOFF_THRESHOLD

    @property
    def current_percentage(self) -> float:
        return self._hub.sensors.power.total.value / self._fuse_max

    @property
    def state_string(self) -> str:
        if not self.enabled:
            return "Disabled"
        if not self.alive:
            return f"Critical. Lower consumption!"
        if self.active:
            if self.current_percentage >= WARNING_THRESHOLD:
                return f"Warning!"
            return f"Ok"

    @property
    def onephase_amps(self) -> dict:
        return self._get_currently_allowed_amps(self._onephase_amps)

    @property
    def threephase_amps(self) -> dict:
        return self._get_currently_allowed_amps(self._threephase_amps)

    def allow_adjustment(self, current_amps: int, new_amps: int, phase) -> bool:
        """this method returns true if the desired adjustment 'new_amps' is not breaching threshold"""
        if not self._allow_amp_adjustment:
            return False
        _new_power = self._get_power_from_amps(current_amps, new_amps, phase)
        return all(
            [
                self._hub.sensors.power.total.value + _new_power < self._fuse_max * CUTOFF_THRESHOLD,
                self._hub.sensors.power.car.value + _new_power + self._hub.sensors.powersensormovingaverage.value < self._fuse_max * CUTOFF_THRESHOLD,
            ]
        )

    def _get_power_from_amps(self, current_amps, new_amps, phases) -> int:
        #get from dict and diff it. check based on phase-charging.
        return 5

    def _get_currently_allowed_amps(self, amps) -> dict:
        """get the currently allowed amps based on the current power draw"""
        _max = (self._fuse_max * CUTOFF_THRESHOLD)
        return {k: v for (k, v) in amps.items() if k + self._hub.sensors.power.total.value < _max}

    def _set_allowed_amps(self, amps_dict, default_amps) -> dict:
        """only allow amps if user has set this value high enough"""
        if self._fuse_max > 0:
            return {k: v for (k, v) in amps_dict.items() if k < self._fuse_max}
        return default_amps

    def _validate(self):
        if self._fuse_max == 0:
            return
        assert self._fuse_max == FUSES_DICT[self._fuse]
        self._enabled = True
        self._active = True

    """
    1 if trying to raise amps and they would hit mains-treshold, dont raise
    2 if approaching mains-threshold on current amps. Lower if possible, else turn off
    """
