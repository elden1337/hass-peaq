
from datetime import datetime


class LocaleTypeBase:
    def __init__(self, observedpeak:str, chargedpeak:str, freechargepattern:list = []): # pylint:disable=dangerous-default-value
        self._observed_peak = observedpeak
        self._charged_peak = chargedpeak
        self._free_charge_pattern = freechargepattern if freechargepattern is not None else []

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
