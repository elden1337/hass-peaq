from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
QUERYTYPE_AVERAGEOFTHREEDAYS,
QUERYTYPE_AVERAGEOFTHREEDAYS_MIN
)

class SE_Gothenburg(LocaleTypeBase):
    def __init__(self):
        self.observed_peak = QUERYTYPE_AVERAGEOFTHREEDAYS_MIN
        self.charged_peak = QUERYTYPE_AVERAGEOFTHREEDAYS



