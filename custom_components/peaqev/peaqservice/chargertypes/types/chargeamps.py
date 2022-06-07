import logging

from homeassistant.core import HomeAssistant
from peaqevcore.Models import CHARGERSTATES

from custom_components.peaqev.peaqservice.chargertypes.calltype import CallType
from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
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

"""
This is the class that implements a specific chargertype into peaqev.
Note that you need to change:

-manifest.json: add the domain of the charger to after_dependencies
-constants.py: alter the CHARGERTYPES with a new type-constant for your charger. If not, it will not be selectable in configflow
-chargertypes.py|init: update the clause with your type to return this class as the charger.
"""

HALO = "Halo"
AURA = "Aura"


class ChargeAmps(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass)
        self._hass = hass
        self._chargeramps_type = ""
        self._chargerid = chargerid
        self._chargeamps_connector = 1
        self.getentities(DOMAINNAME, ENTITYENDINGS)
        self._native_chargerstates = NATIVE_CHARGERSTATES
        self._chargerstates[CHARGERSTATES.Idle] = ["available"]
        self._chargerstates[CHARGERSTATES.Connected] = ["connected"]
        self._chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self._chargerstates[CHARGERSTATES.Done] = ["not_available"]

        self.chargerentity = f"sensor.{self._entityschema}_1"
        self._set_chargeamps_type(self.chargerentity)
        self.powermeter = f"sensor.{self._entityschema}_1_power"
        self.powerswitch = self._determine_switch_entity()
        self.ampmeter = "max_current"
        self.ampmeter_is_attribute = True

        servicecall_params = {}
        servicecall_params[CHARGER] = "chargepoint"
        servicecall_params[CHARGERID] = self._chargerid
        servicecall_params[CURRENT] = "max_current"

        _on_off_params = {
            "chargepoint": self._chargerid,
            "connector": self._chargeamps_connector
        }

        _on = CallType("enable", _on_off_params)
        _off = CallType("disable", _on_off_params)

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call=_on,
            off_call=_off,
            allowupdatecurrent= UPDATECURRENT,
            update_current_call="set_max_current",
            update_current_params=servicecall_params
        )

    def _determine_entities(self):
        ret = []
        for e in self._entities:
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
