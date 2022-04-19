from custom_components.peaqev.peaqservice.localetypes.localtypebase import LocalTypeBase
from custom_components.peaqev.peaqservice.util.constants import (
QUERYTYPE_AVERAGEOFTHREEHOURS,
QUERYTYPE_AVERAGEOFTHREEHOURS_MIN
)

class SE_Nacka_normal(LocalTypeBase):
    def __init__(self):
        self.observed_peak = QUERYTYPE_AVERAGEOFTHREEHOURS_MIN
        self.charged_peak = QUERYTYPE_AVERAGEOFTHREEHOURS



class SE_NACKA_timediff(LocalTypeBase):
    pass
    #this clas is for nacka time differentiated peaks.



#https://www.nackaenergi.se/images/downloads/natavgifter/FAQ_NYA_TARIFFER.pdf
