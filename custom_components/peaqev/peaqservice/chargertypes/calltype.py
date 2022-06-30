from dataclasses import dataclass, field

@dataclass
class CallType:
    call: str
    params: dict = field(default_factory=lambda: {})