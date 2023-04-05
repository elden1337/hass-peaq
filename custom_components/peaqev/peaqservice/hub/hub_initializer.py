import logging
import time
from enum import Enum

_LOGGER = logging.getLogger(__name__)


class InitializerTypes(Enum):
    Hours = "Hours"
    CarPowerSensor = "Car powersensor"
    ChargerObjectSwitch = "Chargerobject switch"
    Power = "Power"
    ChargerObject = "Chargerobject"


class HubInitializer:
    initialized_log_last_logged = 0
    not_ready_list_old_state = 0

    def __init__(self, hub):
        self.parent = hub
        self._initialized: bool = False

    def check(self):
        if self._initialized:
            return True

        init_types = {InitializerTypes.Hours: self.parent.hours.is_initialized}
        if hasattr(self.parent.sensors, "carpowersensor"):
            init_types[InitializerTypes.CarPowerSensor] = self.parent.sensors.carpowersensor.is_initialized
        if hasattr(self.parent.sensors, "chargerobject_switch"):
            init_types[
                InitializerTypes.ChargerObjectSwitch
            ] = self.parent.sensors.chargerobject_switch.is_initialized
        if hasattr(self.parent.sensors, "power"):
            init_types[InitializerTypes.Power] = self.parent.sensors.power.is_initialized
        if hasattr(self.parent.sensors, "chargerobject"):
            init_types[InitializerTypes.ChargerObject] = self.parent.sensors.chargerobject.is_initialized

        if all(init_types.values()):
            self._initialized = True
            _LOGGER.info("Hub is ready to use.")
            _LOGGER.debug(
                f"Hub is initialized with {self.parent.options.price.cautionhour_type} as cautionhourtype."
            )
            return True
        return self._scramble_not_initialized(init_types)

    def _scramble_not_initialized(self, init_types) -> bool:
        not_ready = [r.value for r in init_types if init_types[r] is False]
        if any(
            [
                len(not_ready) != self.not_ready_list_old_state,
                self.initialized_log_last_logged - time.time() > 30,
            ]
        ):
            _LOGGER.info(f"Hub is awaiting {not_ready} before being ready to use.")
            self.not_ready_list_old_state = len(not_ready)
            self.initialized_log_last_logged = time.time()
        if InitializerTypes.ChargerObject in not_ready:
            self.parent.chargertype.helper.set_entitiesmodel()
        return False
