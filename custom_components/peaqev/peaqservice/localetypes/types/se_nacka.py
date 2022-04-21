from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
QUERYTYPE_AVERAGEOFTHREEHOURS,
QUERYTYPE_AVERAGEOFTHREEHOURS_MIN
)

class SE_Nacka_normal(LocaleTypeBase):
    def __init__(self):
        observed_peak = QUERYTYPE_AVERAGEOFTHREEHOURS_MIN
        charged_peak = QUERYTYPE_AVERAGEOFTHREEHOURS

        super().__init__(
            observedpeak=observed_peak,
            chargedpeak=charged_peak
        )


class SE_NACKA_timediff(LocaleTypeBase):
    pass
    #this class is for nacka time differentiated peaks.



#https://www.nackaenergi.se/images/downloads/natavgifter/FAQ_NYA_TARIFFER.pdf
