from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
    QUERYTYPE_BASICMAX
)

#dag kl. 06-22 nov-mars                 106,25 kr/kW/mån
#dag kl. 06-22 april-okt                50 kr/kW/mån
#natt kl. 22-06 alla dagar hela året    0 kr/kW/mån

class SE_Bjerke_Energi(LocaleTypeBase):
    def __init__(self):
        observed_peak = QUERYTYPE_BASICMAX
        charged_peak = QUERYTYPE_BASICMAX
        free_charge_pattern = [
            {
                "M": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "D": [0, 1, 2, 3, 4, 5, 6],
                "H": [22, 23, 0, 1, 2, 3, 4, 5]
            }
        ]
        super().__init__(
            observedpeak=observed_peak,
            chargedpeak=charged_peak,
            freechargepattern=free_charge_pattern
        )

"""
Note, high load extra is added from 06-22 during november - march. 
This does not affect the peak, but should in future updates be cause for forced non-/or caution-hours to lessen the cost for the consumer.
"""

#https://www.bjerke-energi.se/elnat/tariffer/effekttariff-fr-o-m-2022-02-01/
