from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocaleTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR
)

class SE_Kristinehamn(LocaleTypeBase):
    def __init__(self):
        observed_peak = QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR
        charged_peak = QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR

        super().__init__(
            observedpeak=observed_peak,
            chargedpeak=charged_peak
        )




"""
https://kristinehamnsenergi.se/elnat/elnatsavgiften/effektavgift-villa-med-bergvarmepump/

vardagar november-mars, kl 07.00-17.00 > highload instead of normal load. other times, normal load
"""
