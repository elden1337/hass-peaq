import logging

from homeassistant.core import HomeAssistant
from peaqevcore.Models import CHARGERSTATES

from custom_components.peaqev.peaqservice.chargertypes.calltype import CallType
from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
    SWITCH,
    CALL
)

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = [] #todo: list all (or many of) the entity_endings that this integration has set in HA, this is to gather the correct entities.
NATIVE_CHARGERSTATES = [] #todo: list all the available chargerstates here
DOMAINNAME = "" #todo: set the domainname as it is written in HA. ocpp?
UPDATECURRENT = True #todo: True if integration allows update of current during charging. False otherwise
#docs: #todo: put links to the native repo here.

"""
The corresponding constant in peaqservice/util/constants.py is what the user picks.
Thereafter, in the init-process this class is picked from chargertypes.py in the parentfolder to this one.
In this one, you need to gather and tell peaq which entities that are supposed to be read from during the service.
Check the todo's throughout this file. I've also altered type of service-call as CALL or SWITCH (switch for this one then) for the on-off calls,
that's shown in charger.py as a clause where this integration will call hass.states.async_set instead of a service-call to turn the charger on/off
"""


class OCPP(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass)
        self._hass = hass
        self._chargerid = chargerid
        self.getentities(DOMAINNAME, ENTITYENDINGS)
        self._native_chargerstates = NATIVE_CHARGERSTATES

        """this is the states-mapping towards the native peaqev-states."""
        self._chargerstates[CHARGERSTATES.Idle] = [] #todo: list the state(s) that would adhere to peaqev "idle" (ie disconnected)
        self._chargerstates[CHARGERSTATES.Connected] = [] #todo: list the state(s) that adhere to peaqev "connected"
        self._chargerstates[CHARGERSTATES.Charging] = [] #todo: list the state(s) that adhere to "currently charging"
        self._chargerstates[CHARGERSTATES.Done] = [] #todo: list the state(s) that adhere to "done/completed"

        self.chargerentity = f"sensor.{self._entityschema}_1" #todo: alter this to match the chargerentity
        self.powermeter = f"sensor.{self._entityschema}_1_power" #todo: alter this to match the powermeter-entity
        self.powerswitch = self._determine_switch_entity()
        self.ampmeter = "max_current" #todo: if updatecurrent is true, type the sensor or attribute that reports the currently set amps from the charger
        self.ampmeter_is_attribute = True #todo: true if above ampmeter is attribute, false if it's own entity
        """
        this will probably have to be rewritten to accommodate the possibility of ampmeter being an attribute, 
        but not bound to the chargeamps-specific entity
        """

        servicecall_params = {}
        """There could be more, or fewer attributes for the servicecall. If needed, add more constants."""
        #servicecall_params[CHARGER] = "chargepoint" #todo
        #servicecall_params[CHARGERID] = self._chargerid #todo
        #servicecall_params[CURRENT] = "max_current" #todo

        _on = CallType(self.powerswitch, {"command": "on"}, SWITCH)
        _off = CallType(self.powerswitch, {"command": "off"}, SWITCH)

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

    def _determine_switch_entity(self):
        """todo: this most definitely have to be altered to accommodate ocpp"""
        ent = self._determine_entities()
        for e in ent:
            if e.startswith("switch."):
                amps = self._hass.states.get(e).attributes.get("max_current")
                if isinstance(amps, int):
                    return e
        raise Exception
