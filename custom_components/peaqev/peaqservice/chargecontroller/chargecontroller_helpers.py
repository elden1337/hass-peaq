from datetime import datetime, timedelta


def defer_start(non_hours: list) -> bool:
    """Defer starting if next hour is a non-hour and minute is 50 or greater, to avoid short running times."""
    if (datetime.now() + timedelta(hours=1)).hour in non_hours:
        return datetime.now().minute >= 50
    return False


def calculate_stop_len(nonhours) -> str:
    ret = ""
    for idx, h in enumerate(nonhours):
        if idx + 1 < len(nonhours):
            if _getuneven(nonhours[idx + 1], nonhours[idx]):
                ret = _get_stopped_string(h)
                break
        elif idx + 1 == len(nonhours):
            ret = _get_stopped_string(h)
            break
    return ret


def _get_stopped_string(h) -> str:
    val = h + 1 if h + 1 < 24 else h + 1 - 24
    if len(str(val)) == 1:
        return f"Charging stopped until 0{val}:00"
    return f"Charging stopped until {val}:00"


def _getuneven(first, second) -> bool:
    if second > first:
        return first - (second - 24) != 1
    return first - second != 1
