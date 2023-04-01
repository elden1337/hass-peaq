from dataclasses import dataclass


@dataclass
class Command:
    command: str
    expiration: float = None
    argument: any = None

    def __eq__(self, other):
        if all([self.command == other.command, self.argument == other.argument]):
            return True
        return False
