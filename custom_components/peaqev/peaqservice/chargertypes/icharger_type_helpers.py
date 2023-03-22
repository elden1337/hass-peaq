import logging

_LOGGER = logging.getLogger(__name__)


def check_required_sensors(required_types: list, sensors: dict) -> bool:
        for required in required_types:
            try:
                assert required in sensors.keys()
            except AssertionError as a:
                _LOGGER.error(f"could not find the required sensor {required} in the set sensors")
                return False
        return True
