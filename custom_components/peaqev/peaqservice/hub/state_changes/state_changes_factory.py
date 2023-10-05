from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.state_changes.istate_changes import \
    StateChangesBase
from custom_components.peaqev.peaqservice.hub.state_changes.state_changes import (
    StateChanges, StateChangesLite, StateChangesLiteNoCharger,
    StateChangesNoCharger)


class StateChangesFactory:
    @staticmethod
    async def async_create(hub: HomeAssistantHub) -> StateChangesBase:
        if all(
            [
                hub.options.peaqev_lite is True,
                hub.chargertype.type is ChargerType.NoCharger,
            ]
        ):
            return StateChangesLiteNoCharger(hub)
        if hub.options.peaqev_lite is True:
            return StateChangesLite(hub)
        if hub.chargertype.type is ChargerType.NoCharger:
            return StateChangesNoCharger(hub)
        return StateChanges(hub)
