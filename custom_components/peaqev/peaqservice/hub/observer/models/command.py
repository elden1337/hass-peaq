from dataclasses import dataclass


@dataclass
class Command:
    command: str
    expiration: float = None
    argument: any = None
