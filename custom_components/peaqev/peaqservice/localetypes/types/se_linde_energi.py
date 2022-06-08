
from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
    QUERYTYPE_BASICMAX
)


class SE_Linde_Energi(LocaleTypeBase):
    def __init__(self):
        observed_peak = QUERYTYPE_BASICMAX
        charged_peak = QUERYTYPE_BASICMAX
        super().__init__(
            observedpeak=observed_peak,
            chargedpeak=charged_peak
        )

#docs: https://www.lindeenergi.se/elnat/elnatspriser/effekttariffer.4.1491a0b016e44ba6ccfe91b4.html

"""
Din effektavgift baseras på din högsta effekttopp per månad, alltså den timme per månad då du använder mest el sammantaget, oavsett tid på dygnet. 
Under perioden november till mars tillkommer en högbelastningslastavgift, så kallad höglasteffekt, då du även debiteras för ditt högst uppmätta timvärde vardagar kl 07:00-19:00.
Under vintermånaderna kan du alltså debiteras för två olika timvärden, beroende på när på dygnet din effekttopp uppmäts.
"""