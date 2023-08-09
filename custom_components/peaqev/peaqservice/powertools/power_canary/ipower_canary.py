from __future__ import annotations

import logging
from abc import abstractmethod

from peaqevcore.models.fuses import Fuses
from peaqevcore.models.phases import Phases

from custom_components.peaqev.peaqservice.powertools.power_canary.const import (
    CRITICAL, CUTOFF_THRESHOLD, DISABLED, OK, WARNING,
    WARNING_THRESHOLD)
from custom_components.peaqev.peaqservice.powertools.power_canary.power_canary_model import \
    PowerCanaryModel
from custom_components.peaqev.peaqservice.powertools.power_canary.smooth_average import \
    SmoothAverage

_LOGGER = logging.getLogger(__name__)


class IPowerCanary:
    _enabled: bool = False

    def __init__(self, hub, fuse_type, allow_amp_adjustment: bool):
        self.hub = hub
        self.model = PowerCanaryModel(
            warning_threshold=WARNING_THRESHOLD,
            cutoff_threshold=CUTOFF_THRESHOLD,
            fuse=Fuses.parse_from_config(fuse_type),
            allow_amp_adjustment=allow_amp_adjustment,
        )
        self._total_power = SmoothAverage(max_age=60, max_samples=30, ignore=0)
        self._validate()

    @property
    @abstractmethod
    def alive(self) -> bool:
        pass

    @property
    @abstractmethod
    def onephase_amps(self) -> dict:
        pass

    @property
    @abstractmethod
    def threephase_amps(self) -> dict:
        pass

    @abstractmethod
    def check_current_percentage(self):
        pass

    @property
    @abstractmethod
    def max_current_amp(self) -> int:
        pass

    @abstractmethod
    def _validate(self):
        pass

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def fuse(self) -> str:
        return self.model.fuse.value

    @property
    def current_percentage(self) -> float:
        try:
            return self._total_power.value / self.model.fuse_max
        except:
            return 0

    @property
    def total_power(self) -> float:
        if self.enabled:
            return self._total_power.value

    @total_power.setter
    def total_power(self, value) -> None:
        if self.enabled:
            self._total_power.add_reading(float(value))
            self.check_current_percentage()

    @property
    def state_string(self) -> str:
        if not self.enabled:
            return DISABLED
        if not self.alive:
            return CRITICAL
        if self.current_percentage >= self.model.warning_threshold:
            return WARNING
        return OK

    def get_max_current_amp(self, phases) -> int:
        match phases:
            case Phases.OnePhase.name:
                return max(self.onephase_amps.values())
            case Phases.ThreePhase.name:
                return max(self.onephase_amps.values())
        return -1

    async def async_allow_adjustment(self, new_amps: int) -> bool:
        """this method returns true if the desired adjustment 'new_amps' is not breaching threshold"""
        if not self.enabled:
            return True
        if not self.model.allow_amp_adjustment:
            return False
        ret = new_amps <= self.max_current_amp
        if ret is False and self.max_current_amp > -1:
            _LOGGER.warning(
                f"Power Canary cannot allow amp-increase due to the current power-draw. max-amp is:{self.max_current_amp} "
            )
        return ret

    def _get_currently_allowed_amps(self, amps, total_power) -> dict:
        """get the currently allowed amps based on the current power draw"""
        _max = self.model.fuse_max * self.model.cutoff_threshold
        return {k: v for (k, v) in amps.items() if k + total_power < _max}

    """
    1 if trying to raise amps and they would hit mains-treshold, dont raise
    2 if approaching mains-threshold on current amps. Lower if possible, else turn off
    """
