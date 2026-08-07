import logging
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

def defer_start(non_hours: list[datetime]) -> bool:
    """Defer starting if next hour is a non-hour and minute is 50 or greater, to avoid short running times."""
    # non_hours holds datetimes on the hour, both for regular and price aware
    # hours, so the next hour has to be compared as a datetime as well.
    next_hour = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    if next_hour in non_hours:
        if datetime.now().minute >= 50:
            return True
    return False
