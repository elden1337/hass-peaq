from enum import Enum


class CHARGECONTROLLER(Enum):
    Idle = 0
    Connected = 1
    Start = 2
    Stop = 3
    Done = 4
    Error = 5
    Charging = 6
