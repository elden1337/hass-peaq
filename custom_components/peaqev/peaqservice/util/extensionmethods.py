import time
import logging

_LOGGER = logging.getLogger(__name__)

def nametoid(input_string) -> str:
    if isinstance(input_string, str):
        return input_string.lower().replace(" ", "_").replace(",", "")
    return input_string


def dt_from_epoch(epoch: float) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch))


ALREADY_LOGGED = []

def log_once(msg):
    if msg not in ALREADY_LOGGED:
        ALREADY_LOGGED.append(msg)
        _LOGGER.debug(msg)