from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocalTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
QUERYTYPE_BASICMAX
)

class SE_Partille(LocalTypeBase):
    def __init__(self):
        self.observed_peak = QUERYTYPE_BASICMAX
        self.charged_peak = QUERYTYPE_BASICMAX



