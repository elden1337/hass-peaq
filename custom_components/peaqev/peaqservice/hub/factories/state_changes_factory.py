from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import IStateChanges
from custom_components.peaqev.peaqservice.hub.state_changes.state_changes import StateChanges, StateChangesLite, \
    StateChangesNoCharger, StateChangesLiteNoCharger


class StateChangesFactory:

    @staticmethod
    async def async_create(hub) -> IStateChanges:
        if all([
            hub.options.peaqev_lite is True,
            hub.chargertype.type is ChargerType.NoCharger
        ]):
            return StateChangesLiteNoCharger(hub)
        if hub.options.peaqev_lite is True:
            return StateChangesLite(hub)
        if hub.chargertype.type is ChargerType.NoCharger:
            return StateChangesNoCharger(hub)
        return StateChanges(hub)