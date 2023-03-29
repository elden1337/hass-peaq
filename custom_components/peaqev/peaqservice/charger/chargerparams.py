from dataclasses import dataclass

from peaqevcore.models.chargecontroller_states import ChargeControllerStates


@dataclass
class ChargerParams:
    running: bool = False
    disable_current_updates: bool = False
    session_active: bool = False
    latest_charger_call: int = 0
    lastest_call_off: int = 0
    charger_state_mismatch: bool = False
    chargecontroller_state: ChargeControllerStates = ChargeControllerStates.Idle
