from dataclasses import dataclass, field

from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.hub.models.event_property import EventProperty


@dataclass
class HubModel:
    domain: str
    hass: HomeAssistant
    chargingtracker_entities: list = field(default_factory=lambda: [])
    peak_breached: EventProperty = field(init=False)

    def __post_init__(self):
        self.peak_breached = EventProperty(
            "peak_breached",
            bool,
            self.hass,
            False)
