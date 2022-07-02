import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import entity_sources
from peaqevcore.chargertype_service.chargertype_base import ChargerBase
from peaqevcore.chargertype_service.models.calltype import CallType
from peaqevcore.chargertype_service.models.servicecalls_dto import ServiceCallsDTO
from peaqevcore.chargertype_service.models.servicecalls_options import ServiceCallsOptions
from peaqevcore.models.chargerstates import CHARGERSTATES

import custom_components.peaqev.peaqservice.chargertypes.entitieshelper as helper
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = ["_power", "_1", "_2", "_status", "_dimmer", "_downlight", "_current", "_voltage"]
NATIVE_CHARGERSTATES = ["available", "connected", "charging"]
DOMAINNAME = "chargeamps"
UPDATECURRENT = True
#docs: https://github.com/kirei/hass-chargeamps

HALO = "Halo"
AURA = "Aura"


class ChargeAmps(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        self._hass = hass
        self._chargeramps_type = ""
        self._chargerid = chargerid
        self._chargeamps_connector = 1

        self.domainname = DOMAINNAME
        self.entities.imported_entityendings = ENTITYENDINGS
        self.options.powerswitch_controls_charging = True
        self.native_chargerstates = NATIVE_CHARGERSTATES
        self.chargerstates[CHARGERSTATES.Idle] = ["available"]
        self.chargerstates[CHARGERSTATES.Connected] = ["connected"]
        self.chargerstates[CHARGERSTATES.Charging] = ["charging"]

        entitiesobj = helper.getentities(
            self._hass,
            helper.EntitiesPostModel(
                self.domainname,
                self.entities.entityschema,
                self.entities.imported_entityendings
            )
        )
        self.entities.imported_entities = entitiesobj.imported_entities
        self.entities.entityschema = entitiesobj.entityschema

        self.set_sensors()

        servicecall_params = {
            CHARGER: "chargepoint",
            CHARGERID: self._chargerid,
            CURRENT: "max_current"
        }

        _on_off_params = {
            "chargepoint": self._chargerid,
            "connector": self._chargeamps_connector
        }

        self._set_servicecalls(
            domain=DOMAINNAME,
            model=ServiceCallsDTO(
                on=CallType("enable", _on_off_params),
                off=CallType("disable", _on_off_params),
                update_current=CallType("set_max_current", servicecall_params)
            ),
            options=ServiceCallsOptions(
                allowupdatecurrent=UPDATECURRENT,
                update_current_on_termination=True
            )
        )

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

                self.entities.entityschema = candidate
                _LOGGER.debug(f"entityschema is: {self.entities.entityschema} at {time.time()}")
                self.entities.imported_entities = entities

    def _get_entities_from_hass(self, domain_name) -> list:
        return [
            entity_id
            for entity_id, info in entity_sources(self._hass).items()
            if info["domain"] == domain_name
               or info["domain"] == domain_name.capitalize()
               or info["domain"] == domain_name.upper()
               or info["domain"] == domain_name.lower()
        ]

    def set_sensors(self):
        self.entities.chargerentity = f"sensor.{self.entities.entityschema}_1"
        self._set_chargeamps_type(self.entities.chargerentity)
        self.entities.powermeter = f"sensor.{self.entities.entityschema}_1_power"
        self.entities.powerswitch = self._determine_switch_entity()
        self.entities.ampmeter = "max_current"
        self.options.ampmeter_is_attribute = True

    def _determine_entities(self):
        ret = []
        for e in self.entities.imported_entities:
            entity_state = self._hass.states.get(e)
            if entity_state != "unavailable":
                ret.append(e)
        return ret

    def _set_chargeamps_type(self, main_sensor_entity):
        if self._hass.states.get(main_sensor_entity) is not None:
            chargeampstype = self._hass.states.get(main_sensor_entity).attributes.get("chargepoint_type")
            if chargeampstype == "HALO":
                self._chargeramps_type = HALO
            elif chargeampstype == "AURA":
                self._chargeramps_type = AURA


    def _determine_switch_entity(self):
        ent = self._determine_entities()
        for e in ent:
            if e.startswith("switch."):
                amps = self._hass.states.get(e).attributes.get("max_current")
                if isinstance(amps, int):
                    return e
        raise Exception
