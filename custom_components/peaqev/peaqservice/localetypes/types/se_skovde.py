from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
    QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22
)


class SE_Skovde(LocaleTypeBase):
    def __init__(self):
        observed_peak = QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22
        charged_peak = QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22
        free_charge_pattern = [
            {
                "M": [11, 12, 1, 2, 3],
                "D": [5, 6],
                "H": [22, 23, 0, 1, 2, 3, 4, 5]
            },
            {
                "M": [4, 5, 6, 7, 8, 9, 10],
                "D": [0, 1, 2, 3, 4, 5, 6],
                "H": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }
        ]
        super().__init__(
            observedpeak=observed_peak,
            chargedpeak=charged_peak,
            freechargepattern=free_charge_pattern
        )

#November-Mars, vardagar (mån-fre) 06-22
#single peak i denna period månadsvis.

#ticket 22
