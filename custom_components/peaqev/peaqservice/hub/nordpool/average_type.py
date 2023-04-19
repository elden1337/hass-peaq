from enum import Enum


class AverageType(Enum):
    MONTH = "Current month"
    THREE = "3day avg+Current month"
    SEVEN = "7day avg+Current month"
    ERROR = "Error"
