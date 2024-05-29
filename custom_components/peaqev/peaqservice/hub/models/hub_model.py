from dataclasses import dataclass, field

from custom_components.peaqev.peaqservice.hub.models.event_property import \
    EventProperty
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade


@dataclass
class HubModel:
    domain: str
    hass: IHomeAssistantFacade
    chargingtracker_entities: list = field(default_factory=lambda: [])
    peak_breached: EventProperty = field(init=False)

    def __post_init__(self):
        self.peak_breached = EventProperty(
            'peak_breached',
            bool,
            self.hass,
            False)
