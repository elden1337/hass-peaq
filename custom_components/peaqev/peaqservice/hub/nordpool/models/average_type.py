from enum import Enum


class AverageType(Enum):
    MONTH = "30day avg"
    THREE = "3day avg+Current month"
    SEVEN = "7day avg+Current month"
    ERROR = "Error"
