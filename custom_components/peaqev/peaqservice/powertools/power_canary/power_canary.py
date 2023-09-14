from __future__ import annotations

import logging

from custom_components.peaqev.peaqservice.hub.observer.models.observer_types import \
    ObserverTypes
from custom_components.peaqev.peaqservice.powertools.power_canary.const import \
    FUSES_MAX_SINGLE_FUSE
from custom_components.peaqev.peaqservice.powertools.power_canary.ipower_canary import \
    IPowerCanary

_LOGGER = logging.getLogger(__name__)


class PowerCanary(IPowerCanary):
    def __init__(self, hub):
        super().__init__(hub, hub.options.fuse_type, hub.chargertype.servicecalls.options.allowupdatecurrent)

    @property
    def alive(self) -> bool:
        """if returns false no charging can be conducted"""
        if self._enabled is False:
            return True
        return self.hub.sensors.power.total.value < self.model.fuse_max * self.model.cutoff_threshold

    @property
    def onephase_amps(self) -> dict:
        ret = self._get_currently_allowed_amps(self.model.onephase_amps, self.hub.sensors.power.total.value)
        return {k: v for (k, v) in ret.items() if v < FUSES_MAX_SINGLE_FUSE.get(self.model.fuse)}

    @property
    def threephase_amps(self) -> dict:
        return self._get_currently_allowed_amps(self.model.threephase_amps, self.hub.sensors.power.total.value)

    def check_current_percentage(self):
        if not self.alive:
            self.hub.observer.broadcast(command=ObserverTypes.PowerCanaryDead)
        if self.current_percentage >= self.model.warning_threshold:
            self.hub.observer.broadcast(command=ObserverTypes.PowerCanaryWarning)

    @property
    def max_current_amp(self) -> int:
        if not self.enabled:
            return -1
        return self.get_max_current_amp(self.hub.threshold.phases)

    def _validate(self):
        if self.model.fuse_max == 0:
            return
        if self.hub.options.peaqev_lite:
            return
        if self.model.is_valid:
            self._enabled = True
            self._active = True

    """
    1 if trying to raise amps and they would hit mains-treshold, dont raise
    2 if approaching mains-threshold on current amps. Lower if possible, else turn off
    """
