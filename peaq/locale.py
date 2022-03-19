import custom_components.peaq.peaq.constants as constants
from custom_components.peaq.sensors.peaqsqlsensor import (BASICMAX,AVERAGEOFTHREEDAYS,AVERAGEOFTHREEDAYS_MIN,HIGHLOAD)

"""Init the service"""
class LocaleData():
    def __init__(self, input):
        self._ObservedPeak = ""
        self._ChargedPeak = ""
        self._Type = input

        if input == constants.LOCALE_SE_GOTHENBURG:
            self.ObservedPeak = AVERAGEOFTHREEDAYS_MIN
            self.ChargedPeak = AVERAGEOFTHREEDAYS
        elif  input == constants.LOCALE_SE_PARTILLE:
            self.ObservedPeak, self.ChargedPeak = BASICMAX
        elif  input == constants.LOCALE_SE_KARLSTAD:
            self.ObservedPeak = ""
            self.ChargedPeak = ""
        elif  input == constants.LOCALE_SE_KRISTINEHAMN:
            self.ObservedPeak = ""
            self.ChargedPeak = ""
        elif  input == constants.LOCALE_SE_NACKA:
            self.ObservedPeak = ""
            self.ChargedPeak = ""

    @property
    def Type(self) -> str:
        return self._Type
        
    """Observed peak (only added as sensor if separated from charged peak)"""
    @property
    def ObservedPeak(self) -> str:
        return self._ObservedPeak

    @ObservedPeak.setter
    def ObservedPeak(self, val) -> str:
        self._ObservedPeak = val

    """Charged peak (always added)"""
    @property
    def ChargedPeak(self) -> str:
        return self._ChargedPeak

    @ChargedPeak.setter
    def ChargedPeak(self, val) -> str:
        self._ChargedPeak = val

#https://www.nackaenergi.se/images/downloads/natavgifter/FAQ_NYA_TARIFFER.pdf
#https://karlstadsnat.se/elnat/kund/priser-och-tariffer/effekttariff/