
from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
    QUERYTYPE_AVERAGEOFTHREEHOURS_MIN, QUERYTYPE_AVERAGEOFTHREEHOURS
)

#https://www.l-nett.no/nynettleie/slik-blir-ny-nettleie-og-pris

class NO_LNett(LocaleTypeBase):
    def __init__(self):
        observed_peak = QUERYTYPE_AVERAGEOFTHREEHOURS_MIN
        charged_peak = QUERYTYPE_AVERAGEOFTHREEHOURS
        super().__init__(
            observedpeak=observed_peak,
            chargedpeak=charged_peak
        )
