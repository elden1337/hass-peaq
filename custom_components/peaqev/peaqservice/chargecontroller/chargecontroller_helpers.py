import logging
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

def defer_start(non_hours: list) -> bool:
    """Defer starting if next hour is a non-hour and minute is 50 or greater, to avoid short running times."""
    if (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0) in non_hours:
        if datetime.now().minute >= 50:
            return True
    return False
