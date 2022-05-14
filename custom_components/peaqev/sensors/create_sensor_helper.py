import logging

import sqlalchemy
from homeassistant.components.recorder import DEFAULT_DB_FILE, DEFAULT_URL
from sqlalchemy.orm import scoped_session, sessionmaker

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import (
    DOMAIN)
from custom_components.peaqev.peaqservice.util.constants import (
    CONSUMPTION_TOTAL_NAME,
    CONSUMPTION_INTEGRAL_NAME, TYPEREGULAR
)
from custom_components.peaqev.peaqservice.util.sqlsensorhelper import SQLSensorHelper
from custom_components.peaqev.sensors.average_sensor import PeaqAverageSensor
from custom_components.peaqev.sensors.integration_sensor import PeaqIntegrationSensor
from custom_components.peaqev.sensors.money_sensor import PeaqMoneySensor
from custom_components.peaqev.sensors.peaq_sensor import PeaqSensor
from custom_components.peaqev.sensors.power_sensor import (PeaqPowerSensor, PeaqAmpSensor, PeaqHousePowerSensor)
from custom_components.peaqev.sensors.prediction_sensor import PeaqPredictionSensor
from custom_components.peaqev.sensors.sql_sensor import PeaqSQLSensor
from custom_components.peaqev.sensors.threshold_sensor import PeaqThresholdSensor

_LOGGER = logging.getLogger(__name__)

async def gather_sql_sensors(hass, hub, entry_id):
    ret = []
    peaks = hub.locale.data

    db_url = DEFAULT_URL.format(hass_config_path=hass.config.path(DEFAULT_DB_FILE))
    engine = sqlalchemy.create_engine(db_url)
    sessmaker = scoped_session(sessionmaker(bind=engine))
    sqlsensor = hub.totalhourlyenergy.entity
    sql = SQLSensorHelper(sqlsensor).getquerytype(peaks.charged_peak)
    ret.append(PeaqSQLSensor(hub, sessmaker, sql, entry_id))

    if peaks.charged_peak != peaks.observed_peak:
        sql2 = SQLSensorHelper(sqlsensor).getquerytype(peaks.observed_peak)
        ret.append(PeaqSQLSensor(hub, sessmaker, sql2, entry_id))
    return ret

async def gather_Sensors(hub, config) -> list:
    ret = []

    ret.append(PeaqAmpSensor(hub, config.entry_id))
    ret.append(PeaqSensor(hub, config.entry_id))
    ret.append(PeaqThresholdSensor(hub, config.entry_id))

    if hub.powersensor_includes_car is True:
        ret.append(PeaqHousePowerSensor(hub, config.entry_id))
    else:
        ret.append(PeaqPowerSensor(hub, config.entry_id))

    if hub.peaqtype_is_lite is False:
        ret.append(PeaqAverageSensor(hub, config.entry_id))
        ret.append(PeaqPredictionSensor(hub, config.entry_id))

    if hub.price_aware is True:
        ret.append(PeaqMoneySensor(hub, config.entry_id))
    return ret

async def gather_integration_sensors(hub, entry_id):
    ret = []

    if hub.powersensor_includes_car is True:
        ret.append(
            PeaqIntegrationSensor(
                hub,
                f"sensor.{DOMAIN}_{hub.power.house.id}",
                f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}",
                entry_id
            )
        )
        ret.append(
            PeaqIntegrationSensor(
                hub,
                hub.power.total.entity,
                f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}",
                entry_id
            )
        )
    else:
        ret.append(
            PeaqIntegrationSensor(
                hub,
                hub.power.house.entity,
                f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}",
                entry_id
            )
        )
        ret.append(
            PeaqIntegrationSensor(
                hub,
                f"sensor.{DOMAIN}_{hub.power.total.id}",
                f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}",
                entry_id
            )
        )
    return ret