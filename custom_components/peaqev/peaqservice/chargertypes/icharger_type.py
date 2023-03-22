import logging
from abc import abstractmethod
from dataclasses import dataclass, field

from homeassistant.core import HomeAssistant
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype_enum import CallTypes

from custom_components.peaqev.peaqservice.chargertypes.charger_type_options import ChargerTypeOptions
from custom_components.peaqev.peaqservice.chargertypes.icharger_type_calls import IChargerTypeCalls
from custom_components.peaqev.peaqservice.chargertypes.icharger_type_helpers import check_required_sensors
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.option_types import OptionTypes
from custom_components.peaqev.peaqservice.chargertypes.models.sensor_types import SensorTypes

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = []
NATIVE_CHARGERSTATES = []
SENSORS_SCHEMA: dict[SensorTypes, str] = {}
OPTIONS_SCHEMA: dict[OptionTypes, any] = {}
CHARGERSTATES_SCHEMA: dict[ChargeControllerStates, list] = {}
CALLS_SCHEMA: dict[CallTypes, dict] = {}
REQUIRED_SENSORTYPES = [SensorTypes.ChargerEntity, SensorTypes.PowerSwitch]


@dataclass
class IChargerType(IChargerTypeCalls):
    _type: ChargerType
    _domainname: str
    huboptions: HubOptions
    hass: HomeAssistant
    _sensors: dict = field(init=False)
    options: ChargerTypeOptions = field(init=False)
    chargerstates: dict = field(init=False)

    def __post_init__(self):
        self.__setup_sensors()
        self.__setup_options()
        self.__setup_charger_states()
        super().__init__(schema=self.__setup_calls())

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return self._domainname

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return ENTITYENDINGS

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return NATIVE_CHARGERSTATES

    @abstractmethod
    def get_allowed_amps(self) -> int:
        pass

    def __setup_sensors(self) -> None:
        self._sensors = {}
        for type in SENSORS_SCHEMA:
            self._sensors[type] = SENSORS_SCHEMA.get(type).format(self.huboptions.charger.chargerid)
        check_required_sensors(REQUIRED_SENSORTYPES, self._sensors)

    def __setup_options(self) -> None:
        options = ChargerTypeOptions()
        for option in OPTIONS_SCHEMA:
            options.__setattr__(ChargerTypeOptions.get_param(option), OPTIONS_SCHEMA.get(option))
        self.options = options

    def __setup_charger_states(self) -> None:
        self.chargerstates = {}
        for state in ChargeControllerStates:
            self.chargerstates[state] = CHARGERSTATES_SCHEMA.get(state, [])

    def __setup_calls(self) -> dict:
        ret = {}
        for key, value in CALLS_SCHEMA.items():
            ret[key] = self.__setup_calls_recursive(calls=value)
        return ret

    def __setup_calls_recursive(self, calls: dict) -> dict:
        _ret = {}
        for key, value in calls.items():
            if isinstance(value, dict):
                _ret[key] = self.__setup_calls_recursive(calls=value)
            else:
                _ret[key] = self.__set_calls_leaf(call=value)
        return _ret

    def __set_calls_leaf(self, call):
        if str(call).startswith('>'):
            try:
                return self.__dict__[str(call).split('>')[1]]
            except KeyError:
                _LOGGER.exception(f"key {call} not found as referable property")
        return call
