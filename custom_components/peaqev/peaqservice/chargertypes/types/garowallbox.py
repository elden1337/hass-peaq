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
from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade
from custom_components.peaqev.peaqservice.util.constants import (CHARGER,
                                                                 CHARGERID,
                                                                 CURRENT)

_LOGGER = logging.getLogger(__name__)
# docs: https://github.com/sockless-coding/garo_wallbox/

SET_MODE = 'set_mode'
MODE = 'mode'
ENTITY_ID = 'entity_id'
LIMIT = 'limit'


class GaroWallBox(IChargerType):
    def __init__(self, hass: IHomeAssistantFacade, huboptions: HubOptions, chargertype, observer: IObserver):
        _LOGGER.warning(
            'You are initiating GaroWallbox as Chargertype. Bare in mind that this chargertype has not been signed off in testing and may be very unstable. Report findings to the developer.'
        )
        self.observer = observer
        self._hass = hass
        self._is_initialized = False
        self._type = chargertype
        self._chargerid = huboptions.charger.chargerid
        self.entities.imported_entityendings = self.entity_endings
        self.options.powerswitch_controls_charging = False
        self._set_charger_states()

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return 'garo_wallbox'

    @property
    def max_amps(self) -> int:
        return self.get_allowed_amps()

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return [
            '_temperature',
            '_total_energy_kwh',
            '_total_energy',
            '_session_energy',
            '_pilot_level',
            '_current_limit',
            '_phases',
            '_charging_power',
            '_charging_current',
            '_status',
        ]

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return [
            'cable fault',
            'changing...',
            'charging',
            'charging cancelled',
            'charging finished',
            'charging paused',
            'charging disabled',
            'vehicle connected',
            'contactor fault',
            'overtemperature, charging cancelled',
            'dc error',
            'charger starting...',
            'lock fault',
            'vehicle not connected',
            'overtemperature, charging temporarily restricted to 6A',
            'rcd fault',
            'ventilation required',
            'unavailable',
            'unknown',
        ]

    @property
    def call_on(self) -> CallType:
        return CallType(SET_MODE, {MODE: 'On', ENTITY_ID: self._chargerid})

    @property
    def call_off(self) -> CallType:
        return CallType(SET_MODE, {MODE: 'Off', ENTITY_ID: self._chargerid})

    @property
    def call_resume(self) -> CallType:
        return self.call_on

    @property
    def call_pause(self) -> CallType:
        return self.call_off

    @property
    def call_update_current(self) -> CallType:
        return CallType(
            'set_current_limit',
            {
                CHARGER: ENTITY_ID,
                CHARGERID: self._chargerid,  # sensor for garo, not id
                CURRENT: LIMIT,
            },
        )

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=True,
            update_current_on_termination=True,
            switch_controls_charger=False,
        )

    def get_allowed_amps(self) -> int:
        return 16

    def _determine_entities(self) -> list:
        ret = []
        for e in self.entities.imported_entities:
            entity_state = self._hass.get_state(e)
            if entity_state != 'unavailable':
                ret.append(e)
        return ret

    async def async_set_sensors(self) -> None:
        self.entities.chargerentity = f'sensor.{self.entities.entityschema}_status'
        self.entities.powermeter = f'sensor.{self.entities.entityschema}_charging_power'
        self.options.powermeter_factor = 1
        self.entities.ampmeter = f'sensor.{self.entities.entityschema}_charging_current'

        # maybe not? The sensor shows On/Off, but it is not a switch
        self.entities.powerswitch = f'sensor.{self.entities.entityschema}'

    async def async_determine_switch_entity(self) -> str:
        ent = await self.async_determine_entities()
        for e in ent:
            if e.startswith('switch.'):
                amps = self._hass.get_state(e).attributes.get('max_current')
                if isinstance(amps, int):
                    return e
        raise Exception

    async def async_determine_entities(self) -> list:
        ret = []
        for e in self.entities.imported_entities:
            entity_state = self._hass.get_state(e)
            if entity_state != 'unavailable':
                ret.append(e)
        return ret

    def _set_charger_states(self) -> None:
        self.chargerstates[ChargeControllerStates.Idle] = [
            'vehicle not connected',  # vehicle not plugged in
            'charging paused'  # charging disabled by load balancer
        ]
        self.chargerstates[ChargeControllerStates.Connected] = [
            'vehicle connected',  # waiting for start from vehicle (battery full)
            'charging cancelled',  # ?
            'charging disabled'  # charging off (disabled or out of schedule) in Garo GUI
        ]
        self.chargerstates[ChargeControllerStates.Done] = ['charging finished']  # stopped by vehicle
        self.chargerstates[ChargeControllerStates.Charging] = ['charging']
