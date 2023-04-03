import logging
import time

_LOGGER = logging.getLogger(__name__)

def nametoid(input_string) -> str:
    if isinstance(input_string, str):
        return input_string.lower().replace(" ", "_").replace(",", "")
    return input_string


def dt_from_epoch(epoch: float) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch))


ALREADY_LOGGED = {}

def log_once_per_minute(msg):
    """log max once per 1 minutes."""
    if any([
        msg not in ALREADY_LOGGED.keys,
        time.time() - ALREADY_LOGGED[msg] > 60
    ]):
        ALREADY_LOGGED[msg] = time.time()
        _LOGGER.debug(msg)
