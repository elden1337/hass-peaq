from dataclasses import dataclass


@dataclass
class ChargerModel:
    running: bool = False
    disable_current_updates: bool = False
    session_active: bool = False
    latest_charger_call: float = 0
    lastest_call_off: float = 0
    unsuccessful_stop: bool = False
