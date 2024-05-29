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
from custom_components.peaqev.peaqservice.util.constants import (CHARGER,
                                                                 CHARGERID,
                                                                 CURRENT)

_LOGGER = logging.getLogger(__name__)
# docs: https://github.com/fondberg/easee_hass

CHARGER_ID = 'charger_id'
ACTION_COMMAND = 'action_command'


class Easee(IChargerType):
    def __init__(
        self,
        hass: IHomeAssistantFacade,
        huboptions: HubOptions,
        chargertype,
        auth_required: bool = False,
    ):
        self._hass = hass
        self._type = chargertype
        self._chargerid = huboptions.charger.chargerid
        self._auth_required = auth_required
        self.options.powerswitch_controls_charging = False
        self.entities.imported_entityendings = self.entity_endings
        self.chargerstates[ChargeControllerStates.Idle] = ['disconnected']
        self.chargerstates[ChargeControllerStates.Connected] = [
            'awaiting_start',
            'ready_to_charge',
        ]
        self.chargerstates[ChargeControllerStates.Charging] = ['charging']
        self.chargerstates[ChargeControllerStates.Done] = ['completed']
        self._easee_max_amps = None

    @property
    def max_amps(self) -> int:
        if self._easee_max_amps is None:
            return self.get_allowed_amps()
        return self._easee_max_amps

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return 'easee'

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return [
            '_dimmer',
            '_downlight',
            '_current',
            '_voltage',
            '_output_limit',
            '_cost_per_kwh',
            '_enable_idle_current',
            '_is_enabled',
            '_cable_locked_permanently',
            '_smart_charging',
            '_max_charger_limit',
            '_energy_per_hour',
            '_lifetime_energy',
            '_session_energy',
            '_power',
            '_status',
            '_online',
            '_cable_locked',
        ]

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return [
            'disconnected',
            'awaiting_start',
            'charging',
            'ready_to_charge',
            'completed',
            'error',
        ]

    @property
    def call_on(self) -> CallType:
        return CallType(ACTION_COMMAND, {CHARGER_ID: self._chargerid, ACTION_COMMAND: 'start'})

    @property
    def call_off(self) -> CallType:
        return CallType(ACTION_COMMAND, {CHARGER_ID: self._chargerid, ACTION_COMMAND: 'stop'})

    @property
    def call_resume(self) -> CallType:
        return CallType(ACTION_COMMAND, {CHARGER_ID: self._chargerid, ACTION_COMMAND: 'resume'})

    @property
    def call_pause(self) -> CallType:
        return CallType(ACTION_COMMAND, {CHARGER_ID: self._chargerid, ACTION_COMMAND: 'pause'})

    @property
    def call_update_current(self) -> CallType:
        return CallType(
            'set_charger_dynamic_limit',
            {CHARGER: CHARGER_ID, CHARGERID: self._chargerid, CURRENT: 'current'},
        )

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=True,
            update_current_on_termination=False,
            switch_controls_charger=False,
        )

    async def async_set_sensors(self):
        amp_sensor = f'sensor.{self.entities.entityschema}_dynamic_charger_limit'
        if not await self.async_validate_sensor(amp_sensor):
            amp_sensor = f'sensor.{self.entities.entityschema}_max_charger_limit'
        self.entities.maxamps = f'sensor.{self.entities.entityschema}_status|circuit_ratedCurrent'
        self.entities.chargerentity = f'sensor.{self.entities.entityschema}_status'
        self.entities.powermeter = f'sensor.{self.entities.entityschema}_power'
        self.options.powermeter_factor = 1000
        self.entities.powerswitch = f'switch.{self.entities.entityschema}_is_enabled'
        self.entities.ampmeter = amp_sensor

    def get_allowed_amps(self) -> int:
        entity = self.entities.maxamps.split('|')
        state = self._hass.get_state(entity[0])
        ret = 16
        if state is not None:
            retattr = state.attributes.get(entity[1], None)
            if retattr is not None:
                _LOGGER.info(f'Got max amps from Easee. Setting {retattr}A.')
                ret = int(retattr)
                self._easee_max_amps = ret
        else:
            _LOGGER.warning(
                f'Unable to get max amps. The sensor {self.entities.maxamps} returned state {ret}. Setting max amps to 16 til I get a proper state.'
            )
        return ret

    async def async_validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.get_state(sensor)
        if ret is None:
            return False
        if ret.state.lower() in ['null', 'unavailable']:
            return False
        return True
