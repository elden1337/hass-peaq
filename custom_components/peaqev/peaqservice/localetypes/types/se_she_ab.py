from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19,
QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN
)


class SE_SHE_AB(LocaleTypeBase):
    def __init__(self):
        observed_peak = QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN
        charged_peak = QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19
        free_charge_pattern = [
            {
                "M": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "D": [5, 6],
                "H": [19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6]
            }
        ]
        super().__init__(
            observedpeak=observed_peak,
            chargedpeak=charged_peak,
            freechargepattern=free_charge_pattern
        )

"""
Elnätskunder med effekttaxa får vinterpris på överföringsavgift från och med 1 november – 31 mars. 
Prishöjningen på effekttaxan skedde 1 april men blir mer kännbart när vinterpriset nu träder i kraft. 
Kunder som bor i villa och har effekttaxa kan påverka sin kostnad genom att försöka skjuta på sådan förbrukning 
som är möjlig från dagtid till kvällstid (19.00-07:00) eller till helger och röda dagar då det är helt kostnadsfritt att använda elnätet.

Överföringsavgiften beräknas på medelmånadsvärdet av de tre högsta effektvärden dagtid vardagar mellan 07.00-19.00.
"""

"""
Nov – Mars vardagar kl 7-19 135,00 kr/kW inkl moms
April – Okt vardagar kl 7-19 56,00 kr/kW inkl moms
"""
