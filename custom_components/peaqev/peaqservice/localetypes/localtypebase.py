from enum import Enum
from datetime import datetime

"""Determine how the peaks are charger. Monthly, weekly, bi-weekly."""
class PeakChargeType(Enum):
    Monthly = 1,
    Weekly = 2,
    BiWeekly = 3


"""Determine how the peaks are read. Hourly to reset every hours, etc"""
class PeakReaderType(Enum):
    Hourly = 60,
    Quarterly = 15,
    MidHourly = 30


class LocaleTypeBase:
    def __init__(self):
        self._observed_peak = ""
        self._charged_peak = ""
        self._peakcharge_type = PeakChargeType.Monthly
        self._peakreader_type = PeakReaderType.Hourly
        self._free_charge_pattern = []

    """Observed peak (only added as sensor if separated from charged peak)"""
    @property
    def observed_peak(self) -> str:
        return self._observed_peak

    @observed_peak.setter
    def observed_peak(self, val):
        self._observed_peak = val

    """Charged peak (always added)"""
    @property
    def charged_peak(self) -> str:
        return self._charged_peak

    @charged_peak.setter
    def charged_peak(self, val):
        self._charged_peak = val

    @property
    def current_hour_is_free_charge(self) -> bool:
        return self._gather_free_charge_pattern()

    @property
    def ChargeType(self) -> PeakChargeType:
        return self._peakcharge_type

    @property
    def ReaderType(self) -> PeakReaderType:
        return self._peakreader_type

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

