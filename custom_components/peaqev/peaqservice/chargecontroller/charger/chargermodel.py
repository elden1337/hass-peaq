from dataclasses import dataclass


@dataclass
class ChargerModel:
    running: bool = False
    disable_current_updates: bool = False
    session_active: bool = False
    latest_charger_call: int = 0
    lastest_call_off: int = 0
    charger_state_mismatch: bool = False
