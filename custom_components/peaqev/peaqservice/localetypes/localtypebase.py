

class LocalTypeBase:
    def __init__(self):
        self._observed_peak = ""
        self._charged_peak = ""

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