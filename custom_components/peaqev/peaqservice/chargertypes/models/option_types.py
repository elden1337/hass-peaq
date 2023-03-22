from enum import Enum

class OptionTypes(Enum):
    AllowUpdateCurrent = 1
    PowerSwitchControlsCharging = 2
    UpdateCurrentOnTermination = 3
    UseSwitchToggle = 4 #instead of "switch_controls_charger"
    PowerMeterFactor = 5