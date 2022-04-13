from homeassistant.components.sql.sensor import (
    SQLSensor
)
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import (
    SQLSENSOR_BASENAME,
    SQLSENSOR_AVERAGEOFTHREE,
    SQLSENSOR_AVERAGEOFTHREE_MIN,
    SQLSENSOR_HIGHLOAD,
    QUERYTYPE_BASICMAX,
    QUERYTYPE_AVERAGEOFTHREEDAYS,
    QUERYTYPE_AVERAGEOFTHREEDAYS_MIN,
    QUERYTYPE_AVERAGEOFTHREEHOURS,
    QUERYTYPE_AVERAGEOFTHREEHOURS_MIN,
    QUERYTYPE_HIGHLOAD,
    SQLSENSOR_STATISTICS_TABLE,
    SQLSENSOR_STATISTICS_META_TABLE
    )
import custom_components.peaqev.peaqservice.util.extensionmethods as ex

class PeaqSQLSensorHelper():
    def __init__(self, sensor :str):
        self._sensor = ex.nametoid(sensor)
    
    def getquerytype(self, type):
        QUERYTYPES = {
        f"{QUERYTYPE_BASICMAX}" : {
            'query': f'SELECT IFNULL(MAX(state),0) AS state FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id = "{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1',
            'name': f'{SQLSENSOR_BASENAME}'
        },
        f"{QUERYTYPE_AVERAGEOFTHREEDAYS}" : {
            'query': f'SELECT IFNULL(ROUND(AVG(daymax),2),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 3)',
            'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE}'
            },
        f"{QUERYTYPE_AVERAGEOFTHREEHOURS}": {
            'query': f'SELECT IFNULL(ROUND(AVG(daymax),2),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%h\', start) ORDER BY MAX(state) DESC LIMIT 3)',
            'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE}'
        },
        f"{QUERYTYPE_AVERAGEOFTHREEHOURS_MIN}": {
            'query': f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%h\', start) ORDER BY MAX(state) DESC LIMIT 3)',
            'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}'
        },
        f"{QUERYTYPE_AVERAGEOFTHREEDAYS_MIN}" : {
            'query': f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 3)',
            'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}'
        },
        #highload (karlstad etc). Only used Nov - Mar
        f"{QUERYTYPE_HIGHLOAD}" : {
            'query': f'SELECT IFNULL(MAX(state),0) as state FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 8 AND 18 GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1',
            'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_HIGHLOAD}'
            }
        }

        return QUERYTYPES[type]

class PeaqSQLSensor(SQLSensor):
    def __init__(self, hub, sessmaker, query):
        self._hub = hub
        self._attr_name = f"{hub.hubname} {query['name']}"
        self._attr_unique_id = f"{DOMAIN}_{self._hub.hub_id}_{ex.nametoid(self._attr_name)}"
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