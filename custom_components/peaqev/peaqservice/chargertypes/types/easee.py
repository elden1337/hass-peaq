import logging

from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from peaqevcore.Models import CHARGERSTATES
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = ["_power", "_status", "_dimmer", "_downlight", "_lifetime_energy", "_online", "_current", "_voltage", "_output_limit", "_cost_per_kwh", "_enable_idle_current"]
DOMAINNAME = "easee"
UPDATECURRENT = True

"""
UNUSED STATES FROM EASEE

completed
error
"""

class Easee(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid):
        super().__init__(hass)
        self._chargerid = chargerid
        self.getentities(DOMAINNAME, ENTITYENDINGS)
        self._chargerstates[CHARGERSTATES.Idle] = ["disconnected"]
        self._chargerstates[CHARGERSTATES.Connected] = ["awaiting_start", "ready_to_charge"]
        self._chargerstates[CHARGERSTATES.Charging] = ["charging"]
        self.chargerentity = f"sensor.{self._entityschema}_status"
        self.powermeter = f"sensor.{self._entityschema}_power"
        self.powerswitch = f"switch.{self._entityschema}_is_enabled"
        self.ampmeter = f"sensor.{self._entityschema}_max_charger_limit"
        self.ampmeter_is_attribute = False

        servicecall_params = {}
        servicecall_params[CHARGER] = "charger_id"
        servicecall_params[CHARGERID] = self._chargerid
        servicecall_params[CURRENT] = "current"

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call="start",
            off_call="stop",
            pause_call="pause",
            resume_call="resume",
            allowupdatecurrent=True,
            update_current_call="set_charger_dynamic_limit",
            update_current_params=servicecall_params
        )
