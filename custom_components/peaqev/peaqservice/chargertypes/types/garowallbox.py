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

ENTITYENDINGS = [
    '_current_temperature',
    '_latest_reading_k',
    '_latest_reading',
    '_acc_session_energy',
    '_pilot_level',
    '_current_limit',
    '_nr_of_phases',
    '_current_charging_power',
    '_current_charging_current',
    '_status'
 ]

DOMAINNAME = "garo_wallbox"
UPDATECURRENT = True
UPDATECURRENT_ON_TERMINATION = True
#docs: https://github.com/sockless-coding/garo_wallbox/

"""
states:
'CHANGING'
'SEARCH_COMM'
'INITIALIZATION'
'RCD_FAULT'
'DISABLED'
'OVERHEAT'
'CRITICAL_TEMPERATURE'
'CABLE_FAULT'
'LOCK_FAULT'
'CONTACTOR_FAULT'
'VENT_FAULT'
'DC_ERROR'
'UNKNOWN'
'UNAVAILABLE'
"""

class GaroWallbox(ChargerBase):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, auth_required: bool = False):
        self._hass = hass
        self._chargerid = huboptions.charger.chargerid
        self.get_entities()

        self.chargerstates[CHARGERSTATES.Idle] = ['NOT_CONNECTED']
        self.chargerstates[CHARGERSTATES.Connected] = [
            'CONNECTED',
            'CHARGING_PAUSED',
            'CHARGING_CANCELLED'
        ]
        self.chargerstates[CHARGERSTATES.Done] = ['CHARGING_FINISHED']
        self.chargerstates[CHARGERSTATES.Charging] = ['CHARGING']
        self.entities.chargerentity = f"sensor.{self.entities.entityschema}-status"
        self.entities.powermeter = f"sensor.{self.entities.entityschema}-current_charging_power"
        self.options.powermeter_factor = 1

        self.entities.ampmeter = f"sensor.{self.entities.entityschema}-current_charging_current"
        self.options.ampmeter_is_attribute = False
        self.options.powerswitch_controls_charging = False
        self._auth_required = auth_required
        self.entities.powerswitch = "n/a"

        servicecall_params = {
            CHARGER: "entity_id",
            CHARGERID: self._chargerid, #sensor for garo, not id
            CURRENT: "limit"
        }

        _on = CallType("set_mode", {"mode": "on", "entity_id": self.entities.chargerentity})
        _off = CallType("set_mode", {"mode": "off", "entity_id": self.entities.chargerentity})

        self._set_servicecalls(
            domain=DOMAINNAME,
            model=ServiceCallsDTO(
                on=_on,
                off=_off,
                update_current=CallType("set_current_limit", servicecall_params)
            ),
            options=ServiceCallsOptions(
                allowupdatecurrent=UPDATECURRENT,
                update_current_on_termination=UPDATECURRENT_ON_TERMINATION
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
