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
from custom_components.peaqev.peaqservice.chargertypes.models.entities_postmodel import EntitiesPostModel

_LOGGER = logging.getLogger(__name__)

# docs: https://github.com/custom-components/zaptec


class Zaptec(ChargerBase):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, auth_required: bool = False):
        self._hass = hass
        self._chargerid = huboptions.charger.chargerid
        self.entities.imported_entityendings = self.entity_endings
        self._auth_required = auth_required
        self.options.powerswitch_controls_charging = True

        self.chargerstates[CHARGERSTATES.Idle] = ["disconnected"]
        self.chargerstates[CHARGERSTATES.Connected] = ["waiting"]
        self.chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self.chargerstates[CHARGERSTATES.Done] = ["charge_done"]

        entitiesobj = helper.set_entitiesmodel(
            hass=self._hass,
            model=EntitiesPostModel(
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
                resume=self.call_resume,
                pause=self.call_pause
            ),
            options=self.servicecalls_options
        )

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return "zaptec"

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return ["_switch", ""]

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return [
            "unknown",
            "charging",
            "disconnected",
            "waiting",
            "charge_done"
        ]

    @property
    def call_on(self) -> CallType:
        return CallType("start_charging", {"charger_id": self._chargerid})

    @property
    def call_off(self) -> CallType:
        return CallType("stop_charging", {"charger_id": self._chargerid})

    @property
    def call_resume(self) -> CallType:
        return CallType("resume_charging", {"charger_id": self._chargerid})

    @property
    def call_pause(self) -> CallType:
        return CallType("stop_pause_charging", {"charger_id": self._chargerid})

    @property
    def call_update_current(self) -> CallType:
        raise NotImplementedError

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
                allowupdatecurrent=False,
                update_current_on_termination=False,
                switch_controls_charger=False
            )

    def getentities(self, domain: str = None, endings: list = None):
        if len(self.entities.entityschema) < 1:
            domain = self.domain_name if domain is None else domain
            endings = self.entities.imported_entityendings if endings is None else endings

            entities = helper.get_entities_from_hass(
                hass=self._hass,
                domain_name=domain
            )

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
                    _LOGGER.debug(f"entityschema for Zaptec is: {self.entities.entityschema}")
                    self.entities.imported_entities = entities

    def set_sensors(self):
        try:
            self.entities.chargerentity = f"sensor.zaptec_{self.entities.entityschema}"
            self.entities.powermeter = f"{self.entities.chargerentity}|total_charge_power"
            self.options.powermeter_factor = 1
            self.entities.powerswitch = f"switch.zaptec_{self.entities.entityschema}_switch"
            _LOGGER.debug("Sensors for Zaptec have been set up.")
        except Exception as e:
            _LOGGER.exception(f"Could not set needed sensors for Zaptec. {e}")

    def _validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        elif ret.state == "Null":
            return False
        return True
