from dataclasses import dataclass


@dataclass
class ChargerParams:
    running: bool = False
    disable_current_updates: bool = False
    session_active: bool = False
    latest_charger_call: int = 0
    charger_state_mismatch: bool = False