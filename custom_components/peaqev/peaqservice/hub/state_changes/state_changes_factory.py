from custom_components.peaqev.peaqservice.hub.state_changes.state_changes import StateChanges, StateChangesLite, StateChangesNoCharger
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import IStateChanges
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType

class StateChangesFactory:

    @staticmethod
    def create(hub) -> IStateChanges:
        if hub.options.peaqev_lite is True:
            return StateChangesLite(hub)
        elif hub.chargertype.type is ChargerType.NoCharger:
            return StateChangesNoCharger(hub)
        else:
            return StateChanges(hub)