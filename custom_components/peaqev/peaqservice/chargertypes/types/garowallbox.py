import logging
import time

from homeassistant.core import HomeAssistant
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
    def __init__(self, hass: HomeAssistant, chargerid, auth_required: bool = False):
        self._hass = hass
        self._chargerid = chargerid
        self.getentities(DOMAINNAME, ENTITYENDINGS)
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