from dataclasses import dataclass

from custom_components.peaqev.peaqservice.chargertypes.models.option_types import OptionTypes


@dataclass
class ChargerTypeOptions:
    powermeter_factor: int= 1
    """if charger is reporting kW, set to 1000"""
    allow_update_current: bool = False
    powerswitch_controls_charging: bool = False
    update_current_on_termination: bool=False
    """if true, will update current to 6A on termination of charging"""
    use_switch_toggle: bool = False
    """this one determines whether we use a service or a switch to turn charger on/off"""

    @staticmethod
    def get_param(opt: OptionTypes) -> str:
        SCHEMA = {
            OptionTypes.PowerMeterFactor: "powermeter_factor",
            OptionTypes.AllowUpdateCurrent: "allow_update_current",
            OptionTypes.PowerSwitchControlsCharging: "powerswitch_controls_charging",
            OptionTypes.UpdateCurrentOnTermination: "update_current_on_termination",
            OptionTypes.UseSwitchToggle: "use_switch_toggle"
        }
        return SCHEMA.get(opt)