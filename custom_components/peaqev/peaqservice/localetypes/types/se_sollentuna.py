from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
    QUERYTYPE_SOLLENTUNA_MIN, QUERYTYPE_SOLLENTUNA
)

#Rörlig avgift sommar april – oktober 61,46 kr/kW
#Rörlig avgift vinter november – mars 122,92 kr/kW
#https://www.seom.se/el/elnat/2022-ars-priser-och-villkor/

class SE_Sollentuna(LocaleTypeBase):
    def __init__(self):
        observed_peak = QUERYTYPE_SOLLENTUNA_MIN
        charged_peak = QUERYTYPE_SOLLENTUNA
        free_charge_pattern = [
            {
                "M": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "D": [0, 1, 2, 3, 4],
                "H": [19,20,21,22, 23, 0, 1, 2, 3, 4, 5,6]
            },
            {
                "M": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "D": [5, 6],
                "H": [0, 1, 2, 3, 4, 5, 6,7,8,9,10,11,12,13,14,15,16,17,18,19, 20, 21, 22, 23]
            }
        ]
        super().__init__(
            observedpeak=observed_peak,
            chargedpeak=charged_peak,
            freechargepattern=free_charge_pattern
        )
