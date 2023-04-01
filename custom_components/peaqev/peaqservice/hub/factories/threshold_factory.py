
from peaqevcore.services.threshold.threshold import Threshold
from peaqevcore.services.threshold.threshold_lite import ThresholdLite
from peaqevcore.services.threshold.thresholdbase import ThresholdBase


class ThresholdFactory:
    @staticmethod
    async def async_create(hub) -> ThresholdBase:
        if hub.options.peaqev_lite:
            return ThresholdLite(hub)
        else:
            return Threshold(hub)