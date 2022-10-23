import logging

from homeassistant.core import HomeAssistant
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.models.chargerstates import CHARGERSTATES
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import ServiceCallsOptions
from peaqevcore.services.chargertype.chargertype_base import ChargerBase

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
# docs: https://github.com/kirei/hass-chargeamps

HALO = "Halo"
AURA = "Aura"


class ChargeAmps(ChargerBase):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions):
        self._hass = hass
        self._chargeramps_type = ""
        self._chargerid = huboptions.charger.chargerid
        self._chargeamps_connector = 1

        self.domainname = DOMAINNAME
        self.entities.imported_entityendings = ENTITYENDINGS
        self.options.powerswitch_controls_charging = True
        self.native_chargerstates = NATIVE_CHARGERSTATES
        self.chargerstates[CHARGERSTATES.Idle] = ["available"]
        self.chargerstates[CHARGERSTATES.Connected] = ["connected"]
        self.chargerstates[CHARGERSTATES.Charging] = ["charging"]

        self.get_entities()
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
                update_current_on_termination=True,
                switch_controls_charger=False
            )
        )

    def validate_charger(self):
        return True

    def get_entities(self):
        _ret = helper.getentities(
            self._hass,
            helper.EntitiesPostModel(
                domain=self.domainname,
                entityschema=self.entities.entityschema,
                endings=self.entities.imported_entityendings
            )
        )
        self.entities.imported_entities = _ret.imported_entities
        self.entities.entityschema = _ret.entityschema

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
