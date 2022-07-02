import logging

from homeassistant.core import HomeAssistant
from peaqevcore.chargertype_service.chargertype_base import ChargerBase
from peaqevcore.chargertype_service.models.calltype import CallType
from peaqevcore.chargertype_service.models.servicecalls_dto import ServiceCallsDTO
from peaqevcore.chargertype_service.models.servicecalls_options import ServiceCallsOptions
from peaqevcore.models.chargerstates import CHARGERSTATES

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
    def __init__(self, hass: HomeAssistant, chargerid, auth_required: bool = False):
        self._hass = hass
        self._chargerid = chargerid
        self._auth_required = auth_required
        self.options.powerswitch_controls_charging = False
        self.domainname = DOMAINNAME
        self.entities.imported_entityendings = ENTITYENDINGS
        self.native_chargerstates = NATIVE_CHARGERSTATES
        self.chargerstates[CHARGERSTATES.Idle] = ["disconnected"]
        self.chargerstates[CHARGERSTATES.Connected] = ["awaiting_start", "ready_to_charge"]
        self.chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self.chargerstates[CHARGERSTATES.Done] = ["completed"]
        self.getentities()
        self.set_sensors()

        servicecall_params = {
            CHARGER: "charger_id",
            CHARGERID: self._chargerid,
            CURRENT: "current"
        }

        _on_off_params = {"charger_id": self._chargerid}

        _on = CallType("start", _on_off_params)
        _off = CallType("stop", _on_off_params)
        _resume = CallType("set_charger_dynamic_limit", {"current": "7", "charger_id": self._chargerid})
        _pause = CallType("set_charger_dynamic_limit", {"current": "0", "charger_id": self._chargerid})

        self._set_servicecalls(
            domain=DOMAINNAME,
            model=ServiceCallsDTO(
                on=_on if self._auth_required is True else _resume,
                off=_off if self._auth_required is True else _pause,
                pause=_pause,
                resume=_resume,
                update_current=CallType("set_charger_dynamic_limit", servicecall_params)
            ),
            options=ServiceCallsOptions(
                allowupdatecurrent=UPDATECURRENT,
                update_current_on_termination=UPDATECURRENT_ON_TERMINATION
            )
        )

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
