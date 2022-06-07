from datetime import datetime

from homeassistant.components.utility_meter.sensor import (
    QUARTER_HOURLY, HOURLY
)


class LocaleTypeBase:
    def __init__(self, observedpeak:str, chargedpeak:str, peakcycle:str = HOURLY, freechargepattern:list = []): # pylint:disable=dangerous-default-value
        self._observed_peak = observedpeak
        self._charged_peak = chargedpeak
        self._peak_cycle = peakcycle
        self._free_charge_pattern = freechargepattern if freechargepattern is not None else []

    @property
    def is_quarterly(self) -> bool:
        return self.peak_cycle == QUARTER_HOURLY

    @property
    def observed_peak(self) -> str:
        """Observed peak (only added as sensor if separated from charged peak)"""
        return self._observed_peak

    @observed_peak.setter
    def observed_peak(self, val):
        self._observed_peak = val

    @property
    def charged_peak(self) -> str:
        """Charged peak (always added)"""
        return self._charged_peak

    @charged_peak.setter
    def charged_peak(self, val):
        self._charged_peak = val

    @property
    def peak_cycle(self) -> str:
        return self._peak_cycle

    @peak_cycle.setter
    def peak_cycle(self, val):
        self._peak_cycle = val

    @property
    def free_charge(self) -> bool:
        return self._gather_free_charge_pattern()

    def _gather_free_charge_pattern(self) -> bool:
        if len(self._free_charge_pattern) == 0:
            return False

        now = datetime.now()
        for p in self._free_charge_pattern:
            if now.month in p["M"]:
                if now.weekday() in p["D"]:
                    if now.hour in p["H"]:
                        return True

        return False
