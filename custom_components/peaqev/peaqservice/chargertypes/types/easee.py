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
        self.chargerstates = Easee._get_charger_states()

        self.get_entities()
        self._device_id = helper.get_device_id_from_hass(self._hass, self.entities.chargerentity)

        self.validate_charger()

        _call_types = self._get_call_types()
        self._set_servicecalls(
            domain=DOMAINNAME,
            model=ServiceCallsDTO(
                on=_call_types["on"] if self._auth_required is True else _call_types["resume"],
                off=_call_types["off"] if self._auth_required is True else _call_types["pause"],
                pause=_call_types["pause"],
                resume=_call_types["resume"],
                update_current=_call_types["update_current"])
        ,
            options=ServiceCallsOptions(
                allowupdatecurrent=True,
                update_current_on_termination=False,
                switch_controls_charger=False
            )
        )

    @staticmethod
    def _get_charger_states() -> dict:
        chargerstates = {
            CHARGERSTATES.Idle:      ["disconnected"],
            CHARGERSTATES.Connected: ["awaiting_start", "ready_to_charge"],
            CHARGERSTATES.Charging:  ["charging"],
            CHARGERSTATES.Done: ["completed"]
        }
        return chargerstates

    def _get_call_types(self) -> dict[str, CallType]:
        return {
        'on' : CallType("action_command",
                       {
                           "device_id":      self._device_id,
                           "action_command": "start"
                       }),
        'off' : CallType("action_command",
                        {
                            "device_id":      self._device_id,
                            "action_command": "stop"
                        }),
        'resume': CallType("set_charger_dynamic_limit",
                           {
                               "current":   "7",
                               "device_id": self._device_id
                           }),
        'pause': CallType("set_charger_dynamic_limit",
                          {
                              "current":   "0",
                              "device_id": self._device_id
                          }),
        'update_current': CallType("set_charger_dynamic_limit", {
            CHARGER:   "device_id",
            CHARGERID: self._device_id,
            CURRENT:   "current"
        })
        }

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
        _LOGGER.debug(f"schema: {_ret.entityschema}. Imported entities: {_ret.imported_entities}")
        self.entities.imported_entities = _ret.imported_entities
        self.entities.entityschema = _ret.entityschema
        self.set_sensors(_ret.entityschema)

    def set_sensors(self, schema:str):
        amp_sensor = f"sensor.{schema}_dynamic_charger_limit"
        if not self._validate_sensor(amp_sensor):
            amp_sensor = f"sensor.{schema}_max_charger_limit"

        self.entities.chargerentity = f"sensor.{schema}_status"
        self.entities.powermeter = f"sensor.{schema}_power"
        self.options.powermeter_factor = 1000
        self.entities.powerswitch = f"switch.{schema}_is_enabled"
        self.entities.ampmeter = amp_sensor
        self.options.ampmeter_is_attribute = False

    def _validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        if ret.state == "Null":
            return False
        return True
