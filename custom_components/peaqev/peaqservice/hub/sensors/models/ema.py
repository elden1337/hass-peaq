from __future__ import annotations

BASEFACTOR = 4.9204

class EMA:
    def __init__(self, len_avg, smoothing_exp=1, precision=0):
        self._precision = precision
        self.smoothing_factor = self.set_smoothing_factor(len_avg, smoothing_exp)
        self._latest_average = None
        self._imported_average_ready = False

    @property
    def imported_average(self) -> bool:
        return self._imported_average_ready

    @imported_average.setter
    def imported_average(self, value) -> None:
        self._latest_average = value

    @property
    def latest_average(self) -> float:
        return round(self._latest_average, self._precision)

    def set_smoothing_factor(self, len_avg, smoothing_exp) -> float:
        # ret = 2/(len_avg +1) if len_avg > 5000 else (BASEFACTOR/len_avg) / smoothing_exp
        ret = (BASEFACTOR / len_avg) / smoothing_exp
        return ret

    def average(self, sample) -> float:
        if self._latest_average is None:
            self._latest_average = sample
        alpha = self.smoothing_factor
        self._latest_average = alpha * sample + (1 - alpha) * self._latest_average
        return self.latest_average