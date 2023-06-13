import logging
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

def defer_start(non_hours: list) -> bool:
    """Defer starting if next hour is a non-hour and minute is 50 or greater, to avoid short running times."""
    if (datetime.now() + timedelta(hours=1)).hour in non_hours:
        if datetime.now().minute >= 50:
            _LOGGER.debug("Deferring start due to upcoming non-hour")
            return True
    return False
