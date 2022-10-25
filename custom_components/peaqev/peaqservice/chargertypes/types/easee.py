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
    "_dimmer",
    "_downlight",
    "_current",
    "_voltage",
    "_output_limit",
    "_cost_per_kwh",
    "_enable_idle_current",
    "_is_enabled",
    "_cable_locked_permanently",
    "_smart_charging",
    "_max_charger_limit",
    "_energy_per_hour",
    "_lifetime_energy",
    "_session_energy",
    "_power",
    "_status",
    "_online",
    "_cable_locked"
]

NATIVE_CHARGERSTATES = [
    "disconnected",
    "awaiting_start",
    "charging",
    "ready_to_charge",
    "completed",
    "error"
]

DOMAINNAME = "easee"
UPDATECURRENT = True
UPDATECURRENT_ON_TERMINATION = False
#docs: https://github.com/fondberg/easee_hass


class Easee(ChargerBase):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, auth_required: bool = False):
        self._hass = hass
        self._chargerid = huboptions.charger.chargerid
        self._auth_required = auth_required
        self.options.powerswitch_controls_charging = False
        self.domainname = DOMAINNAME
        self.entities.imported_entityendings = ENTITYENDINGS
        self.native_chargerstates = NATIVE_CHARGERSTATES
        self.chargerstates[CHARGERSTATES.Idle] = ["disconnected"]
        self.chargerstates[CHARGERSTATES.Connected] = ["awaiting_start", "ready_to_charge"]
        self.chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self.chargerstates[CHARGERSTATES.Done] = ["completed"]

        self.get_entities()
        self.set_sensors()
        self._device_id = helper.get_device_id_from_hass(self._hass, self.entities.chargerentity)

        if self.validate_charger():
            _on = CallType("action_command",
                           {
                               "device_id": self._chargerid,
                               "action_command": "start"
                           })
            _off = CallType("action_command",
                            {
                                "device_id": self._chargerid,
                                "action_command": "stop"
                            })
            _resume = CallType("set_charger_dynamic_limit",
                               {
                                   "current": "7",
                                   "device_id": self._chargerid
                               })
            _pause = CallType("set_charger_dynamic_limit",
                              {
                                    "current": "0",
                                    "device_id": self._chargerid
                               })
            _update_current = CallType("set_charger_dynamic_limit", {
                CHARGER: "device_id",
                CHARGERID: self._chargerid,
                CURRENT: "current"
            })
            self._set_servicecalls(
                domain=DOMAINNAME,
                model=ServiceCallsDTO(
                    on=_on if self._auth_required is True else _resume,
                    off=_off if self._auth_required is True else _pause,
                    pause=_pause,
                    resume=_resume,
                    update_current=_update_current)
            ,
                options=ServiceCallsOptions(
                    allowupdatecurrent=True,
                    update_current_on_termination=False,
                    switch_controls_charger=False
                )
            )

    def validate_charger(self):
        try:
            assert(self._device_id is not None)
            return True
        except AssertionError as e:
            _LOGGER.exception(f"Can't init Easee due to lack of necessary device-id. Please report to Peaqev-developers. {e}")
            return False

    def get_entities(self):
        _ret = helper.get_entities(
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
        amp_sensor = f"sensor.{self.entities.entityschema}_dynamic_charger_limit"
        if not self._validate_sensor(amp_sensor):
            amp_sensor = f"sensor.{self.entities.entityschema}_max_charger_limit"

        self.entities.chargerentity = f"sensor.{self.entities.entityschema}_status"
        self.entities.powermeter = f"sensor.{self.entities.entityschema}_power"
        self.options.powermeter_factor = 1000
        self.entities.powerswitch = f"switch.{self.entities.entityschema}_is_enabled"
        self.entities.ampmeter = amp_sensor
        self.options.ampmeter_is_attribute = False

    def _validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        if ret.state == "Null":
            return False
        return True
