from datetime import datetime, timedelta


async def async_defer_start(non_hours: list) -> bool:
    """Defer starting if next hour is a non-hour and minute is 50 or greater, to avoid short running times."""
    if (datetime.now() + timedelta(hours=1)).hour in non_hours:
        return datetime.now().minute >= 50
    return False
