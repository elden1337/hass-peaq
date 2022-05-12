from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
QUERYTYPE_AVERAGEOFTHREEDAYS,
QUERYTYPE_AVERAGEOFTHREEDAYS_MIN
)

class SE_Gothenburg(LocaleTypeBase):
    def __init__(self):
        observed_peak = QUERYTYPE_AVERAGEOFTHREEDAYS_MIN
        charged_peak = QUERYTYPE_AVERAGEOFTHREEDAYS

        super().__init__(
            observedpeak=observed_peak,
            chargedpeak=charged_peak
        )
