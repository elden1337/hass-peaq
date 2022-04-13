import custom_components.peaqev.peaqservice.util.constants as constants

"""Init the service"""
class LocaleData():
    def __init__(self, input):
        self._observedpeak = ""
        self._chargedpeak = ""
        self._type = input

        if input == constants.LOCALE_SE_GOTHENBURG:
            self.observedpeak = constants.QUERYTYPE_AVERAGEOFTHREEDAYS_MIN
            self.chargedpeak = constants.QUERYTYPE_AVERAGEOFTHREEDAYS
        elif input == constants.LOCALE_SE_PARTILLE:
            self.observedpeak, self.chargedpeak = constants.QUERYTYPE_BASICMAX
        elif input == constants.LOCALE_SE_KARLSTAD:
            self.observedpeak = ""
            self.chargedpeak = ""
        elif input == constants.LOCALE_SE_KRISTINEHAMN:
            self.observedpeak = ""
            self.chargedpeak = ""
        elif input == constants.LOCALE_SE_NACKA_NORMAL:
            self.observedpeak = constants.QUERYTYPE_AVERAGEOFTHREEHOURS_MIN
            self.chargedpeak = constants.QUERYTYPE_AVERAGEOFTHREEHOURS
        elif input == constants.LOCALE_DEFAULT:
            self.observedpeak, self.chargedpeak = constants.QUERYTYPE_BASICMAX

    @property
    def type(self) -> str:
        return self._type
        
    """Observed peak (only added as sensor if separated from charged peak)"""
    @property
    def observedpeak(self) -> str:
        return self._observedpeak

    @observedpeak.setter
    def observedpeak(self, val) -> str:
        self._observedpeak = val

    """Charged peak (always added)"""
    @property
    def chargedpeak(self) -> str:
        return self._chargedpeak

    @chargedpeak.setter
    def chargedpeak(self, val) -> str:
        self._chargedpeak = val

#https://www.nackaenergi.se/images/downloads/natavgifter/FAQ_NYA_TARIFFER.pdf
#https://karlstadsnat.se/elnat/kund/priser-och-tariffer/effekttariff/