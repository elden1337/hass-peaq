import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ENERGY_KILO_WATT_HOUR
)

from custom_components.peaqev.peaqservice.util.constants import PREDICTION
from custom_components.peaqev.sensors.sensorbase import PowerDevice

_LOGGER = logging.getLogger(__name__)

class PeaqPredictionSensor(PowerDevice):
    device_class = SensorDeviceClass.ENERGY
    unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {PREDICTION}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None

    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:magic-staff"

    def update(self) -> None:
        self._state = self._hub.prediction.predictedenergy  #todo: composition
        #_LOGGER.debug(f"pushing to predictions. minute: {datetime.now().minute}, second: {datetime.now().second}, moving-avg: {self._hub.sensors.powersensormovingaverage.value}, totalhourlyenergy: {self._hub.sensors.totalhourlyenergy.value}, is_quarterly: {self._hub.sensors.locale.data.is_quarterly(self._hub.sensors.locale.data)}")




