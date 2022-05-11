import logging

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.hub.hubdata.hubmember import HubMember
from custom_components.peaqev.peaqservice.util.constants import (TOTALPOWER, HOUSEPOWER)

_LOGGER = logging.getLogger(__name__)

class Power:
    def __init__(self, configsensor: str, powersensor_includes_car: bool = False):
        self._config_sensor = configsensor
        self._total = HubMember(data_type=int, initval=0, name=TOTALPOWER)
        self._house = HubMember(data_type=int, initval=0, name=HOUSEPOWER)
        self._powersensor_includes_car = powersensor_includes_car
        self._setup()

    @property
    def config_sensor(self) -> str:
        return self._config_sensor

    @property
    def total(self) -> HubMember:
        return self._total

    @total.setter
    def total(self, val):
        self._total = val

    @property
    def house(self) -> HubMember:
        return self._house

    @house.setter
    def house(self, val):
        self._house = val

    def _setup(self):
        if self._powersensor_includes_car is True:
            self.total.entity = self.config_sensor
            self.house.entity = ex.nametoid(f"sensor.{DOMAIN}_{HOUSEPOWER}")
        else:
            self.house.entity = self._config_sensor

    def update(self, carpowersensor_value=0, config_sensor_value=None):
        if self._powersensor_includes_car is True:
            if config_sensor_value is not None:
                self.total.value = config_sensor_value
            self.house.value = (float(self.total.value) - float(carpowersensor_value))
        else:
            if config_sensor_value is not None:
                self.house.value = config_sensor_value
            self.total.value = (float(self.house.value) + float(carpowersensor_value))
