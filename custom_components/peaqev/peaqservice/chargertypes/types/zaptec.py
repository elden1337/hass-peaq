import logging

from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.servicecalls_options import \
    ServiceCallsOptions

from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade
from custom_components.peaqev.peaqservice.util.constants import CURRENT

_LOGGER = logging.getLogger(__name__)

# docs: https://github.com/custom-components/zaptec


class Zaptec(IChargerType):
    def __init__(
        self,
        hass: IHomeAssistantFacade,
        huboptions: HubOptions,
        chargertype,
        auth_required: bool = False,
    ):
        _LOGGER.warning(
            'You are initiating Zaptec as Chargertype. Bare in mind that this chargertype has not been signed off in testing and may be very unstable. Report findings to the developer.'
        )
        self._hass = hass
        self._type = chargertype
        self._chargerid = huboptions.charger.chargerid
        self.entities.imported_entityendings = self.entity_endings
        self._auth_required = auth_required
        self.options.powerswitch_controls_charging = True
        self.installation_name = None

        self.chargerstates[ChargeControllerStates.Idle] = ['disconnected']
        self.chargerstates[ChargeControllerStates.Connected] = ['waiting']
        self.chargerstates[ChargeControllerStates.Charging] = ['charging']
        self.chargerstates[ChargeControllerStates.Done] = ['charge_done']

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return 'zaptec'

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return ['_switch', '']

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return ['unknown', 'charging', 'disconnected', 'waiting', 'charge_done']

    @property
    def max_amps(self) -> int:
        return self.get_allowed_amps()

    @property
    def call_on(self) -> CallType:
        return CallType('restart_charger', {'charger_id': self._chargerid})

    @property
    def call_off(self) -> CallType:
        return CallType('stop_charging', {'charger_id': self._chargerid})

    @property
    def call_resume(self) -> CallType:
        return CallType('resume_charging', {'charger_id': self._chargerid})

    @property
    def call_pause(self) -> CallType:
        return CallType('stop_charging', {'charger_id': self._chargerid})

    @property
    def call_update_current(self) -> CallType:
        return CallType('limit_current',{'installation_id': self._chargerid, CURRENT: 'available_current'})

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=True,
            update_current_on_termination=True,
            switch_controls_charger=False,
        )

    def get_allowed_amps(self) -> int:
        """no such method for chargeamps available right now."""
        return 16

    async def async_set_sensors(self):
        try:
            self.entities.chargerentity = f'sensor.{self.entities.entityschema}_charger_mode'
            self.entities.powermeter = f'sensor.{self.entities.chargerentity}_charge_power'
            self.options.powermeter_factor = 1
            self.entities.powerswitch = f'switch.{self.entities.entityschema}_charging'
            self.entities.ampmeter = f'number.{self.installation_name}_available_current' #todo: installation_name is not part of peaqevsetup. how to handle?
            _LOGGER.debug('Sensors for Zaptec have been set up.')
        except Exception as e:
            _LOGGER.exception(f'Could not set needed sensors for Zaptec. {e}')

    def _validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.get_state(sensor)
        if ret is None:
            return False
        elif ret.state == 'Null':
            return False
        return True

    async def async_validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.get_state(sensor)
        if ret is None:
            return False
        elif ret.state == 'Null':
            return False
        return True
