from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
QUERYTYPE_BASICMAX
)

class SE_Partille(LocaleTypeBase):
    def __init__(self):
        self.observed_peak = QUERYTYPE_BASICMAX
        self.charged_peak = QUERYTYPE_BASICMAX



