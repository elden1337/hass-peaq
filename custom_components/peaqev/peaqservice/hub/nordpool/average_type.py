from enum import Enum


class AverageType(Enum):
    MONTH = "Current month"
    THREE = "3day average and current month"
    SEVEN = "7day average and current month"
    ERROR = "Error"
