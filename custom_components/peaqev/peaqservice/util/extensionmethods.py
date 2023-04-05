import logging
import time

_LOGGER = logging.getLogger(__name__)


def nametoid(input_string) -> str:
    if isinstance(input_string, str):
        return input_string.lower().replace(" ", "_").replace(",", "")
    return input_string


def dt_from_epoch(epoch: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch))


already_logged = []


def log_once(msg):
    try:
        if msg not in already_logged:
            already_logged.append(msg)
            _LOGGER.debug(msg)
    except Exception as e:
        _LOGGER.error(f"Error in log_once_per_minute: {e}")
