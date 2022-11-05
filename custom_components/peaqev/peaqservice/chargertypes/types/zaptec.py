import logging

from custom_components.peaqev.peaqservice.chargertypes.calltype import CallType
from homeassistant.core import HomeAssistant
from peaqevcore.Models import CHARGERSTATES
from peaqevcore.hub.hub_options import HubOptions
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

    def set_sensors(self):
        self.entities.chargerentity = f"sensor.zaptec_{self.entities.entityschema}"
        self.entities.powermeter = f"{self.entities.chargerentity}|total_charge_power"
        #self.powermeter_is_attribute = True
        self.options.powermeter_factor = 1
        self.entities.powerswitch = f"switch.zaptec_{self.entities.entityschema}_switch"

    def _validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        elif ret.state == "Null":
            return False
        return True
