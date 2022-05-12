from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
    QUERYTYPE_AVERAGEOFFIVEDAYS,
    QUERYTYPE_AVERAGEOFFIVEDAYS_MIN
)

#Rörlig avgift sommar april – oktober 35 kr/kW
#Rörlig avgift vinter november – mars 118,75 kr/kW

class SE_Malung_Salen(LocaleTypeBase):
    def __init__(self):
        observed_peak = QUERYTYPE_AVERAGEOFFIVEDAYS_MIN
        charged_peak = QUERYTYPE_AVERAGEOFFIVEDAYS
        free_charge_pattern = [
            {
                "M": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "D": [0, 1, 2, 3, 4, 5, 6],
                "H": [19,20,21,22, 23, 0, 1, 2, 3, 4, 5,6]
            }
        ]
        super().__init__(
            observedpeak=observed_peak,
            chargedpeak=charged_peak,
            freechargepattern=free_charge_pattern
        )
