import time
from statistics import mean


class Average:
    def __init__(self, max_age: int, max_samples: int, precision: int = 2):
        self._readings = []
        self._average = 0
        self._max_age = max_age
        self._max_samples = max_samples
        self._precision = precision
        self._latest_update = 0

    @property
    def average(self) -> float:
        self._set_average()
        return round(self._average, self._precision)

    def _set_average(self):
        try:
            self._average = mean([x[1] for x in self._readings])
        except ZeroDivisionError:
            self._average = 0

    def readings(self) -> list:
        return self._readings

    def _remove_from_list(self):
        """Removes overflowing number of samples and old samples from the list."""
        while len(self._readings) > self._max_samples:
            self._readings.pop(0)
        gen = (
            x for x in self._readings if time.time() - int(x[0]) > self._max_age
        )
        for i in gen:
            if len(self._readings) > 1:
                # Always keep one reading
                self._readings.remove(i)

    def add_reading(self, val: float):
        self._readings.append((int(time.time()), round(val, 3)))
        self._latest_update = time.time()
        self._remove_from_list()
        self._set_average()