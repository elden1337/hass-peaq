from __future__ import annotations

BASE_FACTOR = 0.000302204

class EMA:
    def __init__(self, len_avg:float, smoothing_exp:float=1):
        self.smoothing_factor = self.set_smoothing_factor(len_avg, smoothing_exp)
        self._latest_average:float|None = None
        self._imported_average_ready:bool = False

    @property
    def imported_average(self) -> bool:
        return self._imported_average_ready

    @imported_average.setter
    def imported_average(self, value) -> None:
        self._latest_average = value

    @staticmethod
    def set_smoothing_factor(len_avg:float, smoothing_exp:float) -> float:
        ret = 2 / (len_avg + 1) if len_avg > 5000 else BASE_FACTOR * len_avg / smoothing_exp
        return ret

    def average(self, sample) -> float:
        if self._latest_average is None:
            self._latest_average = sample
        alpha = self.smoothing_factor
        self._latest_average = alpha * sample + (1 - alpha) * self._latest_average
        return self._latest_average