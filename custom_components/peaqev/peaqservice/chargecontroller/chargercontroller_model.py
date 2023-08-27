from dataclasses import dataclass

from peaqevcore.common.wait_timer import WaitTimer
from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.chargecontroller.const import DONETIMEOUT
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType


@dataclass
class ChargeControllerModel:
    charger_type: ChargerType  # todo: when chargertype is under chargecontroller this should be removed.
    charger_states: dict
    is_initialized: bool = False
    status_type: ChargeControllerStates = ChargeControllerStates.Idle
    latest_charger_start: WaitTimer = WaitTimer(timeout=DONETIMEOUT)
    latest_debuglog: float = 0
