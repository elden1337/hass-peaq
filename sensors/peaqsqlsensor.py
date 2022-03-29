from homeassistant.components.sql.sensor import (
    SQLSensor
)
from custom_components.peaq.const import DOMAIN
import custom_components.peaq.peaq.constants as constants
import custom_components.peaq.peaq.extensionmethods as ex

class PeaqSQLSensorHelper():
    def __init__(self, sensor :str):
        self._sensor = ex.NameToId(sensor)
    
    def GetQueryType(self, type):
        QUERYTYPES = {
        f"{constants.QUERYTYPES.BASICMAX}" : {
            'query': f'SELECT IFNULL(MAX(state),0) AS state FROM "{constants.SQLSENSOR.STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{constants.SQLSENSOR.STATISTICS_META_TABLE}" WHERE statistic_id = "{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1',
            'name': f'{constants.SQLSENSOR.BASENAME}',
            'entity': ''
        },
        f"{constants.QUERYTYPES.AVERAGEOFTHREEDAYS}" : {
            'query': f'SELECT IFNULL(ROUND(AVG(daymax),2),0) as state FROM ( SELECT MAX(state) as daymax FROM "{constants.SQLSENSOR.STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{constants.SQLSENSOR.STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 3)',
            'name': f'{constants.SQLSENSOR.BASENAME}, Average of three',
            'entity': ''
            },
        f"{constants.QUERYTYPES.AVERAGEOFTHREEDAYS_MIN}" : {
            'query': f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{constants.SQLSENSOR.STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{constants.SQLSENSOR.STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 3)',
            'name': f'{constants.SQLSENSOR.BASENAME}, Min of three',
            'entity': ''
        },
        #höglast (karlstad). Bara i effekt nov tom mars
        f"{constants.QUERYTYPES.HIGHLOAD}" : {
            'query': f'SELECT IFNULL(MAX(state),0) as state FROM "{constants.SQLSENSOR.STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{constants.SQLSENSOR.STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 8 AND 18 GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1',
            'name': f'{constants.SQLSENSOR.BASENAME}, High load',
            'entity': ''
            }
        }

        return QUERYTYPES[type]

class PeaqSQLSensor(SQLSensor):
    def __init__(self, hub, sessmaker, query):
        self._hub = hub
        self._attr_name = f"{hub.hubname} {query['name']}"
        self._attr_unique_id = f"{DOMAIN}_{self._hub.hub_id}_{ex.NameToId(self._attr_name)}"
        sm = sessmaker
        super().__init__(
            self._attr_name,
            sm,
            query["query"],
            "state",
            "kW",
            None
            )

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}