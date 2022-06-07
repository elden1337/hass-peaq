import logging

from homeassistant.core import HomeAssistant
from peaqevcore.Models import CHARGERSTATES

from custom_components.peaqev.peaqservice.chargertypes.calltype import CallType
from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGERID,
    CURRENT,
    SWITCH
)

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = [
    "_reset",
    "_unlock",
    "_maximum_current",
    "_connectors",
    "_current_import",
    "_current_offered",
    "_energy_active_import_register",
    "_energy_meter_start",
    "_energy_session",
    "_error_code",
    "_error_code_connector",
    "_features",
    "_frequency",
    "_heartbeat",
    "_id",
    "_id_tag",
    "_latency_ping",
    "_latency_pong",
    "_model",
    "_power_active_import",
    "_power_offered",
    "_reconnects",
    "_serial",
    "_soc",
    "_status",
    "_status_connector",
    "_status_firmware",
    "_stop_reason",
    "_time_session",
    "_timestamp_config_response",
    "_timestamp_data_response",
    "_timestamp_data_transfer",
    "_transaction_id",
    "_vendor",
    "_version_firmware",
    "_availability",
    "_charge_control"
] #todo: LISTED ALL POSSIBLE. TO BE SORTED WHICH IS NEEDED OR NOT --> list all (or many of) the entity_endings that this integration has set in HA, this is to gather the correct entities.

NATIVE_CHARGERSTATES = ["Available", "Preparing", "Charging", "SuspendedEVSE", "SuspendedEV", "Finishing", "Reserved", "Unavailable", "Faulted"]
DOMAINNAME = "ocpp"
UPDATECURRENT = False #todo: set true later, but for initial testing ignore it.

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
        self._chargerstates[CHARGERSTATES.Idle] = ["Available"]
        self._chargerstates[CHARGERSTATES.Connected] = ["Preparing"]
        self._chargerstates[CHARGERSTATES.Charging] = ["Charging"]
        self._chargerstates[CHARGERSTATES.Done] = ["Finishing"] #todo: need to be tested if there are additional states i.e. what happens after it finished?

        self.chargerentity = f"sensor.{self._entityschema}_id"
        self.powermeter = f"sensor.{self._entityschema}_power_active_import"
        #self.powerswitch = self._determine_switch_entity()
        self.powerswitch = f"switch.{self._entityschema}_charge_control"
        self.ampmeter = f"sensor.{self._entityschema}_current_import"
        self.ampmeter_is_attribute = False

        servicecall_params = {}
        """There could be more, or fewer attributes for the servicecall. If needed, add more constants."""
        #servicecall_params[CHARGER] = "chargepoint" #todo
        servicecall_params[CHARGERID] = self._chargerid
        servicecall_params[CURRENT] = "maximum_current" #not sure about this one

        _on = CallType(self.powerswitch, {"command": "on"}, SWITCH)
        _off = CallType(self.powerswitch, {"command": "off"}, SWITCH)

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call=_on,
            off_call=_off,
            allowupdatecurrent= UPDATECURRENT,
            update_current_call="set_charge_rate",
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
