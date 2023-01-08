import logging
import time

from homeassistant.core import HomeAssistant
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.models.chargerstates import CHARGERSTATES
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import ServiceCallsOptions
from peaqevcore.services.chargertype.chargertype_base import ChargerBase

import custom_components.peaqev.peaqservice.chargertypes.entitieshelper as helper
from custom_components.peaqev.peaqservice.chargertypes.models.chargeamps_types import ChargeAmpsTypes
from custom_components.peaqev.peaqservice.chargertypes.models.entities_postmodel import EntitiesPostModel
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)

_LOGGER = logging.getLogger(__name__)


# docs: https://github.com/kirei/hass-chargeamps


class ChargeAmps(ChargerBase):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions):
        self._hass = hass
        self._chargeramps_type = ""
        self._chargerid = huboptions.charger.chargerid
        self._chargeamps_connector = 1  # fix this later
        self.entities.imported_entityendings = self.entity_endings
        self.options.powerswitch_controls_charging = True
        self.chargerstates[CHARGERSTATES.Idle] = ["available"]
        self.chargerstates[CHARGERSTATES.Connected] = ["connected"]
        self.chargerstates[CHARGERSTATES.Charging] = ["charging"]

        entitiesobj = helper.set_entitiesmodel(
            self._hass,
            EntitiesPostModel(
                self.domain_name,
                self.entities.entityschema,
                self.entities.imported_entityendings
            )
        )
        self.entities.imported_entities = entitiesobj.imported_entities
        self.entities.entityschema = entitiesobj.entityschema

        self.set_sensors()

        self._set_servicecalls(
            domain=self.domain_name,
            model=ServiceCallsDTO(
                on=self.call_on,
                off=self.call_off,
                pause=self.call_pause,
                resume=self.call_resume,
                update_current=self.call_update_current
            ),
            options=self.servicecalls_options
        )

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return "chargeamps"

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return ["_power", "_1", "_2", "_status", "_dimmer", "_downlight", "_current", "_voltage"]

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return ["available", "connected", "charging"]

    @property
    def call_on(self) -> CallType:
        return CallType("enable", {
            "chargepoint": self._chargerid,
            "connector":   self._chargeamps_connector
        })

    @property
    def call_off(self) -> CallType:
        return CallType("disable", {
            "chargepoint": self._chargerid,
            "connector":   self._chargeamps_connector
        })

    @property
    def call_resume(self) -> CallType:
        return self.call_on

    @property
    def call_pause(self) -> CallType:
        return self.call_off

    @property
    def call_update_current(self) -> CallType:
        return CallType("set_max_current", {
            CHARGER:   "chargepoint",
            CHARGERID: self._chargerid,
            CURRENT:   "max_current"
        })

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=True,
            update_current_on_termination=True,
            switch_controls_charger=False
        )

    def get_allowed_amps(self) -> int:
        """no such method for chargeamps available right now."""
        pass

    def getentities(self, domain: str = None, endings: list = None):
        if len(self.entities.entityschema) < 1:
            domain = self.domainname if domain is None else domain
            endings = self.entities.imported_entityendings if endings is None else endings

            entities = helper.get_entities_from_hass(self._hass, domain)

            if len(entities) < 1:
                _LOGGER.error(f"no entities found for {domain} at {time.time()}")
            else:
                _endings = endings
                candidate = ""

                for e in entities:
                    splitted = e.split(".")
                    for ending in _endings:
                        if splitted[1].endswith(ending):
                            candidate = splitted[1].replace(ending, '')
                            break
                    if len(candidate) > 1:
                        break

                if candidate == "":
                    _LOGGER.exception(f"Unable to find valid sensorschema for your {domain}.")
                else:
                    self.entities.entityschema = candidate
                    _LOGGER.debug(f"entityschema is: {self.entities.entityschema} at {time.time()}")
                    self.entities.imported_entities = entities

    def set_sensors(self) -> None:
        self.entities.chargerentity = f"sensor.{self.entities.entityschema}_1"
        self.entities.powermeter = f"sensor.{self.entities.entityschema}_1_power"
        self.entities.ampmeter = "max_current"
        self.options.ampmeter_is_attribute = True
        self.entities.powerswitch = self._determine_switch_entity()
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
