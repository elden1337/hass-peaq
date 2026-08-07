from dataclasses import dataclass
from typing import Any

from peaqevcore.common.models.observer_types import ObserverTypes


@dataclass(frozen=True)
class Command:
    command: ObserverTypes
    expiration: float | None = None
    argument: Any = None

    def __eq__(self, other):
        if all([self.command == other.command, self.argument == other.argument]):
            return True
        return False
