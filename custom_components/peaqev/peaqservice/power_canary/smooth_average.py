import logging
import statistics as stat
import time

_LOGGER = logging.getLogger(__name__)


class SmoothAverage:
    def __init__(self, max_age: int, max_samples: int, precision: int = 2, ignore: int = None):
        self._init_time = time.time()
        self._readings = []
        self._max_age = max_age
        self._max_samples = max_samples
        self._latest_update = 0
        self._ignore = ignore
        self._precision = precision

    @property
    def value(self) -> float | None:
        if len(self._readings) > 0:
            ret = stat.mean([i[1] for i in self._readings])
            if ret == 0:
                _LOGGER.debug(f"Reading was 0. The samples are {self._readings}")
            return ret
        #_LOGGER.debug(f"No readings available for smooth average")
        return None

    @property
    def samples(self) -> int:
        return len(self._readings)

    @property
    def samples_raw(self) -> list:
        return self._readings

    @samples_raw.setter
    def samples_raw(self, lst):
        self._readings.extend(lst)

    @property
    def is_clean(self) -> bool:
        return all(
            [
                time.time() - self._init_time > 300,
                self.samples > 1
            ]
        )

    def add_reading(self, val):
        t = time.time()
        try:
            floatval = float(val)
        except:
            return
        if self._ignore is None or floatval > self._ignore:
            self._readings.append((int(t), floatval))
            self._latest_update = time.time()
            self._remove_from_list()

    def _remove_from_list(self):
        """Removes overflowing number of samples and old samples from the list."""
        while len(self._readings) > self._max_samples:
            self._readings.pop(0)
        gen = (x for x in self._readings if time.time() - int(x[0]) > self._max_age)
        for i in gen:
            if len(self._readings) > 2:
                self._readings.remove(i)

