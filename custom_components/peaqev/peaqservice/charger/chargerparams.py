from dataclasses import dataclass


@dataclass
class ChargerParams:
    running: bool = False
    stopped: bool = False
    disable_current_updates: bool = False
    session_active: bool = False
    latest_charger_call: int = 0
    check_running_state: bool = False