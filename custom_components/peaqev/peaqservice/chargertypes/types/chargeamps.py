import logging

from homeassistant.core import HomeAssistant
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import \
    ServiceCallsOptions

import custom_components.peaqev.peaqservice.chargertypes.entitieshelper as helper
from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargeamps_types import \
    ChargeAmpsTypes
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.util.constants import (CHARGER,
                                                                 CHARGERID,
                                                                 CURRENT)

_LOGGER = logging.getLogger(__name__)
# docs: https://github.com/kirei/hass-chargeamps

CHARGEPOINT = "chargepoint"
CONNECTOR = "connector"


class ChargeAmps(IChargerType):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, chargertype):
        self._hass = hass
        self._type = chargertype
        self._chargeramps_type = ""
        self._chargerid = huboptions.charger.chargerid
        self._chargeamps_connector = 1  # fix this later to be able to use aura
        self.entities.imported_entityendings = self.entity_endings
        self.options.powerswitch_controls_charging = True
        self.chargerstates[ChargeControllerStates.Idle] = ["available"]
        self.chargerstates[ChargeControllerStates.Connected] = ["connected"]
        self.chargerstates[ChargeControllerStates.Charging] = ["charging"]

    async def async_setup(self):
        try:
            entitiesobj = await helper.async_set_entitiesmodel(
                hass=self._hass,
                domain=self.domain_name,
                entity_endings=self.entity_endings,
                entity_schema=self.entities.entityschema,
            )
            self.entities.imported_entities = entitiesobj.imported_entities
            self.entities.entityschema = entitiesobj.entityschema
        except:
            _LOGGER.debug(f"Could not get a proper entityschema for {self.domain_name}.")

        await self.async_set_sensors()

        await self.async_set_servicecalls(
            domain=self.domain_name,
            model=ServiceCallsDTO(
                on=self.call_on,
                off=self.call_off,
                pause=self.call_pause,
                resume=self.call_resume,
                update_current=self.call_update_current,
            ),
            options=self.servicecalls_options,
        )

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return "chargeamps"

    @property
    def max_amps(self) -> int:
        return self.get_allowed_amps()

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return [
            "_power",
            "_1",
            "_2",
            "_status",
            "_dimmer",
            "_downlight",
            "_current",
            "_voltage",
        ]

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return ["available", "connected", "charging"]

    @property
    def call_on(self) -> CallType:
        return CallType(
            "enable",
            {CHARGEPOINT: self._chargerid, CONNECTOR: self._chargeamps_connector},
        )

    @property
    def call_off(self) -> CallType:
        return CallType(
            "disable",
            {CHARGEPOINT: self._chargerid, CONNECTOR: self._chargeamps_connector},
        )

    @property
    def call_resume(self) -> CallType:
        return self.call_on

    @property
    def call_pause(self) -> CallType:
        return self.call_off

    @property
    def call_update_current(self) -> CallType:
        return CallType(
            "set_max_current",
            {CHARGER: CHARGEPOINT, CHARGERID: self._chargerid, CURRENT: "max_current"},
        )

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

    def set_sensors(self) -> None:
        self.entities.chargerentity = f"sensor.{self.entities.entityschema}_1"
        self.entities.powermeter = f"sensor.{self.entities.entityschema}_1_power"
        self.entities.powerswitch = self._determine_switch_entity()
        self.entities.ampmeter = f"{self.entities.powerswitch}|max_current"
        self._chargeramps_type = self._set_chargeamps_type(self.entities.chargerentity)

    def _determine_entities(self) -> list:
        ret = []
        for e in self.entities.imported_entities:
            entity_state = self._hass.states.get(e)
            if entity_state != "unavailable":
                ret.append(e)
        return ret

    def _set_chargeamps_type(self, main_sensor_entity) -> ChargeAmpsTypes:
        if self._hass.states.get(main_sensor_entity) is not None:
            chargeampstype = self._hass.states.get(main_sensor_entity).attributes.get("chargepoint_type")
            return ChargeAmpsTypes.get_type(chargeampstype)

    def _determine_switch_entity(self) -> str:
        ent = self._determine_entities()
        for e in ent:
            if e.startswith("switch."):
                amps = self._hass.states.get(e).attributes.get("max_current")
                if isinstance(amps, int):
                    return e
        raise Exception

    async def async_set_sensors(self) -> None:
        self.entities.chargerentity = f"sensor.{self.entities.entityschema}_1"
        self.entities.powermeter = f"sensor.{self.entities.entityschema}_1_power"
        self.entities.powerswitch = await self.async_determine_switch_entity()
        self.entities.ampmeter = f"{self.entities.powerswitch}|max_current"
        self._chargeramps_type = await self.async_set_chargeamps_type(self.entities.chargerentity)

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

    async def async_set_chargeamps_type(self, main_sensor_entity) -> ChargeAmpsTypes:
        if self._hass.states.get(main_sensor_entity) is not None:
            chargeampstype = self._hass.states.get(main_sensor_entity).attributes.get("chargepoint_type")
            return await ChargeAmpsTypes.async_get_type(chargeampstype)
