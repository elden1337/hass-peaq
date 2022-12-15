# from peaqevcore.models.fuses import Fuses
from __future__ import annotations

import logging

from peaqevcore.models.const import CURRENTS_THREEPHASE_1_32, CURRENTS_THREEPHASE_1_16, CURRENTS_ONEPHASE_1_16, \
    CURRENTS_ONEPHASE_1_32
from peaqevcore.models.phases import Phases

from custom_components.peaqev.peaqservice.power_canary.fuses import Fuses
from custom_components.peaqev.peaqservice.power_canary.smooth_average import SmoothAverage

_LOGGER = logging.getLogger(__name__)

FUSES_DICT = {
    Fuses.FUSE_3_16: 11000,
    Fuses.FUSE_3_20: 14000,
    Fuses.FUSE_3_25: 17000,
    Fuses.FUSE_3_35: 24000,
    Fuses.FUSE_3_50: 35000,
    Fuses.FUSE_3_63: 44000
}

FUSES_MAX_SINGLE_FUSE = {
    Fuses.FUSE_3_16: 16,
    Fuses.FUSE_3_20: 20,
    Fuses.FUSE_3_25: 25,
    Fuses.FUSE_3_35: 35,
    Fuses.FUSE_3_50: 50,
    Fuses.FUSE_3_63: 63
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
        self._total_power = SmoothAverage(max_age=60, max_samples=30, ignore=0)
        self._validate()

    @property
    def total_power(self) -> float:
        if self.enabled and self.active:
            return self._total_power.value

    @total_power.setter
    def total_power(self, value) -> None:
        if self.enabled and self.active:
            self._total_power.add_reading(float(value))
            self.check_current_percentage()

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
        try:
            return self._total_power.value / self._fuse_max
        except:
            return 0

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
        ret = self._get_currently_allowed_amps(self._onephase_amps)
        return {k: v for (k, v) in ret.items() if v < FUSES_MAX_SINGLE_FUSE[self._fuse]}

    @property
    def threephase_amps(self) -> dict:
        return self._get_currently_allowed_amps(self._threephase_amps)

    def check_current_percentage(self):
        if not self.alive:
            # turn_off
            pass
        if self.current_percentage >= WARNING_THRESHOLD:
            # lower or turn_off
            #self._hub.charger._updatemaxcurrent()
            pass

    def allow_adjustment(self, new_amps: int) -> bool:
        """this method returns true if the desired adjustment 'new_amps' is not breaching threshold"""
        if not self.active:
            return True
        if not self._allow_amp_adjustment:
            return False

        max_amps = 0
        match self._hub.threshold.phases:
            case Phases.OnePhase:
                max_amps = max(self.onephase_amps.values())
            case Phases.ThreePhase:
                max_amps = max(self.onephase_amps.values())

        ret = new_amps <= max_amps

        if ret is False:
            _LOGGER.info(f"Power Canary cannot allow amp-increase due to the current power-draw.")
        else:
            _LOGGER.debug(f"Power Canary allows charger to set {new_amps}A for {self._hub.threshold.phases.value}.")
        return ret

    def _get_currently_allowed_amps(self, amps) -> dict:
        """get the currently allowed amps based on the current power draw"""
        _max = (self._fuse_max * CUTOFF_THRESHOLD)
        return {k: v for (k, v) in amps.items() if k + self._hub.sensors.power.total.value < _max}

    def _set_allowed_amps(self, amps_dict, default_amps) -> dict:
        """only allow amps if user has set this value high enough"""
        if self._fuse_max > 0:
            return {k: v for (k, v) in default_amps.items() if k < self._fuse_max}
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
