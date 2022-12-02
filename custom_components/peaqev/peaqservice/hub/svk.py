import time
from datetime import datetime

from peaqevcore.services.locale.Locale import (
    LOCALE_SE_ESKILSTUNA,
    LOCALE_SE_GOTHENBURG,
    LOCALE_SE_KARLSTAD,
    LOCALE_SE_KRISTINEHAMN,
    LOCALE_SE_NACKA_NORMAL,
    LOCALE_SE_PARTILLE,
    LOCALE_SE_SALA,
    LOCALE_SE_MALUNG_SALEN,
    LOCALE_SE_TEKNISKA_LINK,
    LOCALE_SE_SKOVDE,
    LOCALE_SE_SOLLENTUNA,
    LOCALE_SE_BJERKE_ENERGI,
    LOCALE_SE_LINDE_ENERGI,
    LOCALE_SE_FALBYDGENS_ENERGI,
    LOCALE_SE_MALARENERGI
)


class svk:
    def __init__(self, hub):
        self.hub = hub
        self.hours = [8, 9, 10, 16, 17, 18]
        self.weekdays = [0, 1, 2, 3, 4]
        self.stopdate = 1680300000
        self.localelist = [LOCALE_SE_ESKILSTUNA,LOCALE_SE_GOTHENBURG,LOCALE_SE_KARLSTAD,LOCALE_SE_KRISTINEHAMN,LOCALE_SE_NACKA_NORMAL,LOCALE_SE_PARTILLE,
                            LOCALE_SE_SALA,LOCALE_SE_MALUNG_SALEN,LOCALE_SE_TEKNISKA_LINK,LOCALE_SE_SKOVDE,LOCALE_SE_SOLLENTUNA,
                            LOCALE_SE_BJERKE_ENERGI,LOCALE_SE_LINDE_ENERGI,LOCALE_SE_FALBYDGENS_ENERGI,LOCALE_SE_MALARENERGI]

    @property
    def should_stop(self):
        if not self.hub.options.locale in self.localelist:
            return False
        if time.time() > self.stopdate:
            return False
        _now = datetime.now()
        if _now.weekday() in self.weekdays:
            if _now.hour in self.hours:
                return True
        return False

    @property
    def stopped_string(self):
        return "Stoppad pga höglasttimme"