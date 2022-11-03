import logging

from custom_components.peaqev.peaqservice.chargertypes.calltype import CallType
from homeassistant.core import HomeAssistant
from peaqevcore.Models import CHARGERSTATES
from peaqevcore.hub.hub_options import HubOptions

import custom_components.peaqev.peaqservice.chargertypes.entitieshelper as helper
from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase

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
        self._powerswitch_controls_charging = False
        self._domainname = DOMAINNAME
        self.entities.imported_entityendings = ENTITYENDINGS
        self._native_chargerstates = NATIVE_CHARGERSTATES
        self._chargerstates[CHARGERSTATES.Idle] = ["disconnected"]
        self._chargerstates[CHARGERSTATES.Connected] = ["waiting"]
        self._chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self._chargerstates[CHARGERSTATES.Done] = ["charge_done"]

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

        _on = CallType("start_charging", _on_off_params)
        _off = CallType("stop_charging", _on_off_params)
        _resume = CallType("resume_charging", _on_off_params)
        _pause = CallType("stop_pause_charging", _on_off_params)

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call=_on,
            off_call=_off,
            pause_call=_pause,
            resume_call=_resume,
            allowupdatecurrent=UPDATECURRENT
        )

    def set_sensors(self):
        self.chargerentity = f"sensor.zaptec_{self._entityschema}"
        self.powermeter = "total_charge_power" #attribute on chargerentity
        self.powermeter_is_attribute = True
        self.powermeter_factor = 1
        self.powerswitch = f"switch.zaptec_{self._entityschema}_switch"

    def _validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        elif ret.state == "Null":
            return False
        return True
