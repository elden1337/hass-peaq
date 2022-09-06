from dataclasses import dataclass


@dataclass
class ChargerParams:
    _running: bool = False
    _stopped: bool = False
    _disable_current_updates: bool = False
    _session_active: bool  = False
    _latest_charger_call: int = 0
    _check_running_state: bool = False