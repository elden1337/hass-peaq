from enum import Enum

class OptionTypes(Enum):
    AllowUpdateCurrent = 1
    AmpMeterIsAttribute = 2
    PowerSwitchControlsCharging = 3
    UpdateCurrentOnTermination = 4
    UseSwitchToggle = 5 #instead of "switch_controls_charger"
    PowerMeterFactor = 6