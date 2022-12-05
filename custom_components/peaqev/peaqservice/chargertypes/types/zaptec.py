import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import entity_sources
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.models.chargerstates import CHARGERSTATES
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import ServiceCallsOptions
from peaqevcore.services.chargertype.chargertype_base import ChargerBase

import custom_components.peaqev.peaqservice.chargertypes.entitieshelper as helper

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = [
    "_switch"
]

NATIVE_CHARGERSTATES = [
"unknown",
"charging",
"disconnected",
"waiting",
"charge_done"
]

DOMAINNAME = "zaptec"
UPDATECURRENT = False
UPDATECURRENT_ON_TERMINATION = False
#docs: https://github.com/custom-components/zaptec


class Zaptec(ChargerBase):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, auth_required: bool = False):
        super().__init__(hass)
        self._hass = hass
        self._chargerid = huboptions.charger.chargerid
        self._auth_required = auth_required
        self._domainname = DOMAINNAME
        self.entities.imported_entityendings = ENTITYENDINGS
        self._native_chargerstates = NATIVE_CHARGERSTATES
        self.chargerstates[CHARGERSTATES.Idle] = ["disconnected"]
        self.chargerstates[CHARGERSTATES.Connected] = ["waiting"]
        self.chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self.chargerstates[CHARGERSTATES.Done] = ["charge_done"]

        self.set_sensors()

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

        _on_off_params = {"charger_id": self._chargerid}

        self._set_servicecalls(
            domain=DOMAINNAME,
            model=ServiceCallsDTO(
                on=CallType("start_charging", _on_off_params),
                off=CallType("stop_charging", _on_off_params),
                resume=CallType("resume_charging", _on_off_params),
                pause=CallType("stop_pause_charging", _on_off_params)
            ),
            options=ServiceCallsOptions(
                allowupdatecurrent=UPDATECURRENT,
                update_current_on_termination=UPDATECURRENT_ON_TERMINATION,
                switch_controls_charger=False
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
        self.entities.chargerentity = f"sensor.zaptec_charger_{self.entities.entityschema}"
        self.entities.powermeter = f"{self.entities.chargerentity}|total_charge_power"
        self.options.powermeter_factor = 1
        self.entities.powerswitch = f"switch.zaptec_{self.entities.entityschema}_switch"

    def _validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        elif ret.state == "Null":
            return False
        return True
