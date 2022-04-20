from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
    QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22
)

class SE_Skovde(LocaleTypeBase):
    def __init__(self):
        self.observed_peak = QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22
        self.charged_peak = QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22


#November-Mars, vardagar (mån-fre) 06-22
#single peak i denna period månadsvis.

#ticket 22