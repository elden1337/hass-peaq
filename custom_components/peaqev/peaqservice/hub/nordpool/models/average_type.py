from enum import Enum


class AverageType(Enum):
    MONTH = "Current month"
    THREE = "3day avg"
    SEVEN = "7day avg"
    THIRTY = "30day avg"
    ERROR = "Error"
