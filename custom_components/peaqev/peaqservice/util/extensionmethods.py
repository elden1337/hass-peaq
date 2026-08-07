import inspect
import logging
import time
from functools import partial

_LOGGER = logging.getLogger(__name__)


def nametoid(input_string) -> str:
    if isinstance(input_string, str):
        return input_string.lower().replace(' ', '_').replace(',', '')
    return input_string


def dt_from_epoch(epoch: float) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch))


def try_parse_float(value) -> float | None:
    """Parse a restored state, which may well be 'unknown' or 'unavailable'.

    Raising inside async_added_to_hass makes Home Assistant drop the entity
    altogether, so restoring has to tolerate a non-numeric state.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


already_logged = {}


def log_once_per_minute(msg, level):
    global already_logged
    try:
        if msg not in already_logged.keys():
            already_logged[msg] = time.time()
            log_func = getattr(_LOGGER, level, _LOGGER.info)
            log_func(msg)
        already_logged = {k: v for k, v in already_logged.items() if v > time.time() - 60}
    except Exception as e:
        _LOGGER.error(f'Error in log_once_per_minute: {e}')


async def async_iscoroutine(object):
    while isinstance(object, partial):
        object = object.func
    return inspect.iscoroutinefunction(object)
