from dataclasses import dataclass, field

@dataclass
class ObserverModel:
    subscribers: dict = field(default_factory=lambda: {})
    broadcast_queue: list = field(default_factory=lambda: [])
    wait_queue: dict = field(default_factory=lambda: {})
    active: bool = False
    