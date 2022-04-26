from datetime import datetime
from peaqevcore.Prediction import PredictionBase as core_prediction


class Prediction():
    def __init__(self, hub=None):
        self._hub = hub
    
    @property
    def predictedenergy(self) -> float:
        return core_prediction.predictedenergy(
            datetime.now().minute,
            datetime.now().second,
            self._hub.powersensormovingaverage.value if self._hub.powersensormovingaverage.value is not None else 0,
            self._hub.totalhourlyenergy.value
        )

    @property
    def predictedpercentageofpeak(self) -> float:
        return core_prediction.predictedpercentageofpeak(
            self._hub.currentpeak.value,
            self.predictedenergy
        )