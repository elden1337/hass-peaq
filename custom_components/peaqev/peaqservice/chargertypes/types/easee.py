import logging

from homeassistant.core import HomeAssistant
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.calltype_enum import CallTypes
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import ServiceCallsOptions

import custom_components.peaqev.peaqservice.chargertypes.entitieshelper as helper
from custom_components.peaqev.peaqservice.chargertypes.icharger_type import IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)

_LOGGER = logging.getLogger(__name__)
# docs: https://github.com/fondberg/easee_hass

CHARGER_ID = "charger_id"
ACTION_COMMAND = "action_command"


class Easee(IChargerType):
    _chargerid = None

    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, chargertype, auth_required: bool = False):
        self._hass = hass
        self._type = chargertype
        self._chargerid = huboptions.charger.chargerid
        self._auth_required = auth_required
        self.options.powerswitch_controls_charging = False
        self.entities.imported_entityendings = self.entity_endings
        self.chargerstates[ChargeControllerStates.Idle] = ["disconnected"]
        self.chargerstates[ChargeControllerStates.Connected] = ["awaiting_start", "ready_to_charge"]
        self.chargerstates[ChargeControllerStates.Charging] = ["charging"]
        self.chargerstates[ChargeControllerStates.Done] = ["completed"]

        try:
            entitiesobj = helper.set_entitiesmodel(
                hass=self._hass,
                domain=self.domain_name,
                entity_endings=self.entity_endings,
                entity_schema=self.entities.entityschema
            )
            self.entities.imported_entities = entitiesobj.imported_entities
            self.entities.entityschema = entitiesobj.entityschema
        except:
            _LOGGER.debug(f"Could not get a proper entityschema for {self.domain_name}.")

        self._set_sensors(self.entities.entityschema)
        self._set_servicecalls(
            domain=self.domain_name,
            model=ServiceCallsDTO(
                on=self.call_on if self._auth_required is True else self.call_resume,
                off=self.call_off if self._auth_required is True else self.call_pause,
                pause=self.call_pause,
                resume=self.call_resume,
                update_current=self.call_update_current
            ),
            options=self.servicecalls_options
        )

    _calls = {
        CallTypes.On:            CallType(ACTION_COMMAND, {
            CHARGER_ID:     _chargerid,
            ACTION_COMMAND: "start"
        }),
        CallTypes.Off:           CallType(ACTION_COMMAND, {
            CHARGER_ID:     _chargerid,
            ACTION_COMMAND: "stop"
        }),
        CallTypes.Resume:        CallType("set_charger_dynamic_limit", {
            "current":  "7",
            CHARGER_ID: _chargerid
        }),
        CallTypes.Pause:         CallType("set_charger_dynamic_limit", {
            "current":  "0",
            CHARGER_ID: _chargerid
        }),
        CallTypes.UpdateCurrent: CallType("set_charger_dynamic_limit", {
            CHARGER:   CHARGER_ID,
            CHARGERID: _chargerid,
            CURRENT:   "current"
        })
    }

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return "easee"

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return [
            "_dimmer", "_downlight",
            "_current", "_voltage",
            "_output_limit", "_cost_per_kwh",
            "_enable_idle_current", "_is_enabled",
            "_cable_locked_permanently", "_smart_charging",
            "_max_charger_limit", "_energy_per_hour",
            "_lifetime_energy", "_session_energy",
            "_power", "_status",
            "_online", "_cable_locked"
        ]

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return [
            "disconnected",
            "awaiting_start",
            "charging",
            "ready_to_charge",
            "completed",
            "error"
        ]

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=True,
            update_current_on_termination=False,
            switch_controls_charger=False
        )

    def _set_sensors(self, schema):
        amp_sensor = f"sensor.{schema}_dynamic_charger_limit"
        if not self._validate_sensor(amp_sensor):
            amp_sensor = f"sensor.{schema}_max_charger_limit"
        self.entities.maxamps = f"sensor.{schema}_max_charger_limit"
        self.entities.chargerentity = f"sensor.{schema}_status"
        self.entities.powermeter = f"sensor.{schema}_power"
        self.options.powermeter_factor = 1000
        self.entities.powerswitch = f"switch.{schema}_is_enabled"
        self.entities.ampmeter = amp_sensor
        self.options.ampmeter_is_attribute = False

    def _get_allowed_amps(self) -> int:
        ret = self._hass.states.get(self.entities.maxamps)
        if ret is not None:
            return min(32, int(ret.state))
        else:
            _LOGGER.warning("Unable to get max amps for circuit. Setting max amps to 16.")
        return 16

    def _validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        if ret.state.lower() in ["null", "unavailable"]:
            return False
        return True
