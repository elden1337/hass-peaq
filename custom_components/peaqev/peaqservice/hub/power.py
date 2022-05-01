from custom_components.peaqev.peaqservice.hub.hubmember import HubMember
from custom_components.peaqev.peaqservice.util.constants import (TOTALPOWER,HOUSEPOWER)


class Power:
    def __init__(self, configsensor: str, powersensor_includes_car: bool = False):
        self._config_sensor = configsensor
        self._mock_house_sensor = None
        self._total = HubMember(type=int, initval=0, name=TOTALPOWER)
        self._house = HubMember(type=int, initval=0, name=HOUSEPOWER)
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
            self._mock_house_sensor = self._create_mock_house_sensor()
        else:
            self.house.entity = self._config_sensor
            self._mock_house_sensor = self._config_sensor

    def _create_mock_house_sensor(self) -> str:
        pass

    def update(self, carpowersensor_value=0, val=None):
        if self._powersensor_includes_car is True:
            if val is not None:
                self.total.value = val
            self.house.value = (self.total.value - carpowersensor_value)
        else:
            if val is not None:
                self.house.value = val
            self.total.value = (self.house.value + carpowersensor_value)
