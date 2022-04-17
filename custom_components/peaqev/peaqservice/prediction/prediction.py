from datetime import datetime
from custom_components.peaqev.peaqservice.prediction.predictionbase import PredictionBase


class Prediction(PredictionBase):
    def __init__(self, hub=None):
        self._hub = hub
    
    @property
    def predictedenergy(self) -> float:
        return self._predictedenergy(
            datetime.now().minute,
            datetime.now().second,
            self._hub.powersensormovingaverage.value if self._hub.powersensormovingaverage.value is not None else 0,
            self._hub.totalhourlyenergy.value
        )

    @property
    def predictedpercentageofpeak(self) -> float:
        return self._predictedpercentageofpeak(
            self._hub.currentpeak.value,
            self.predictedenergy
        )