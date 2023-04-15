from dataclasses import dataclass, field

from custom_components.peaqev.peaqservice.hub.observer.models.command import \
    Command


@dataclass
class ObserverModel:
    subscribers: dict = field(default_factory=lambda: {})
    broadcast_queue: list[Command] = field(default_factory=lambda: [])
    wait_queue: dict[str, float] = field(default_factory=lambda: {})
    active: bool = False
