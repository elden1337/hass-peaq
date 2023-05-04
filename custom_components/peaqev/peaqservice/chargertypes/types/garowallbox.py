import logging

from homeassistant.core import HomeAssistant
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.servicecalls_options import ServiceCallsOptions

from custom_components.peaqev.peaqservice.chargertypes.icharger_type import IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import (
    ChargerType,
)
from custom_components.peaqev.peaqservice.hub.models.hub_options import HubOptions
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)

_LOGGER = logging.getLogger(__name__)
# docs: https://github.com/sockless-coding/garo_wallbox/

SET_MODE = "set_mode"
MODE = "mode"
ENTITY_ID = "entity_id"
LIMIT = "limit"


class GaroWallBox(IChargerType):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, chargertype):
        _LOGGER.warning(
            "You are initiating GaroWallbox as Chargertype. Bare in mind that this chargertype has not been signed off in testing and may be very unstable. Report findings to the developer."
        )
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
        return "garo_wallbox"

    @property
    def max_amps(self) -> int:
        return self.get_allowed_amps()

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return [
            "_current_temperature",
            "_latest_reading_k",
            "_latest_reading",
            "_acc_session_energy",
            "_pilot_level",
            "_current_limit",
            "_nr_of_phases",
            "_current_charging_power",
            "_current_charging_current",
            "_status",
        ]

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return [
            "CHANGING",
            "NOT_CONNECTED",
            "CONNECTED",
            "SEARCH_COMM",
            "RCD_FAULT",
            "CHARGING",
            "CHARGING_PAUSED",
            "CHARGING_FINISHED",
            "CHARGING_CANCELLED",
            "DISABLED",
            "OVERHEAT",
            "CRITICAL_TEMPERATURE",
            "INITIALIZATION",
            "CABLE_FAULT",
            "LOCK_FAULT",
            "CONTACTOR_FAULT",
            "VENT_FAULT",
            "DC_ERROR",
            "UNKNOWN",
            "UNAVAILABLE",
        ]

    @property
    def call_on(self) -> CallType:
        return CallType(SET_MODE, {MODE: "on", ENTITY_ID: self.entities.chargerentity})

    @property
    def call_off(self) -> CallType:
        return CallType(SET_MODE, {MODE: "off", ENTITY_ID: self.entities.chargerentity})

    @property
    def call_resume(self) -> CallType:
        return self.call_on

    @property
    def call_pause(self) -> CallType:
        return self.call_off

    @property
    def call_update_current(self) -> CallType:
        return CallType(
            "set_current_limit",
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
            entity_state = self._hass.states.get(e)
            if entity_state != "unavailable":
                ret.append(e)
        return ret

    async def async_set_sensors(self) -> None:
        self.entities.chargerentity = f"sensor.{self.entities.entityschema}-status"
        self.entities.powermeter = (
            f"sensor.{self.entities.entityschema}-current_charging_power"
        )
        self.options.powermeter_factor = 1
        self.entities.ampmeter = (
            f"sensor.{self.entities.entityschema}-current_charging_current"
        )
        self.entities.powerswitch = "n/a"

    async def async_determine_switch_entity(self) -> str:
        ent = await self.async_determine_entities()
        for e in ent:
            if e.startswith("switch."):
                amps = self._hass.states.get(e).attributes.get("max_current")
                if isinstance(amps, int):
                    return e
        raise Exception

    async def async_determine_entities(self) -> list:
        ret = []
        for e in self.entities.imported_entities:
            entity_state = self._hass.states.get(e)
            if entity_state != "unavailable":
                ret.append(e)
        return ret

    def _set_charger_states(self) -> None:
        self.chargerstates[ChargeControllerStates.Idle] = ["NOT_CONNECTED"]
        self.chargerstates[ChargeControllerStates.Connected] = [
            "CONNECTED",
            "CHARGING_PAUSED",
            "CHARGING_CANCELLED",
        ]
        self.chargerstates[ChargeControllerStates.Done] = ["CHARGING_FINISHED"]
        self.chargerstates[ChargeControllerStates.Charging] = ["CHARGING"]
