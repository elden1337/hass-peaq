import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

DEFAULT_OVERRIDE = 1
MONTHS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
}

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=False)
class Timer:
    expire:datetime = datetime.now()

    @property
    def is_override(self) -> bool:
        return self.expire > datetime.now()

    @property
    def override_string(self) -> str:
        if self.expire.day != datetime.now().day:
            _dt = f"{self.expire.day} {MONTHS[self.expire.month]} - {self.expire.hour}:{self.expire.minute}"
        else:
            _dt = f"{self.expire.hour}:{self.expire.minute}"
        return f"Nonhours ignored until {_dt}"

    def update(self, value_in_hours:int=DEFAULT_OVERRIDE):
        try:
            assert isinstance(value_in_hours, int)
        except AssertionError as a:
            _LOGGER.debug(a)
            return
        value_in_seconds = value_in_hours * 3600
        self.expire += timedelta(seconds=value_in_seconds)
