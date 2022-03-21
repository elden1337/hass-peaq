"""Platform for sensor integration."""
import logging
from custom_components.peaq.sensors.peaqutilitysensor import (
    PeaqUtilitySensor,
    METER_OFFSET,
    PERIODS
)

from custom_components.peaq.sensors.peaqintegrationsensor import PeaqIntegrationSensor
from custom_components.peaq.sensors.peaqaveragesensor import PeaqAverageSensor
from custom_components.peaq.sensors.peaqsqlsensor import (PeaqSQLSensor, PeaqSQLSensorHelper)
from custom_components.peaq.sensors.peaqpowersensor import (PeaqPowerSensor, PeaqAmpSensor)
from custom_components.peaq.sensors.peaqpredictionsensor import PeaqPredictionSensor
from custom_components.peaq.sensors.peaqthresholdsensor import PeaqThresholdSensor
from custom_components.peaq.sensors.peaqsensor import PeaqSensor
import custom_components.peaq.peaq.extensionmethods as ex

from homeassistant.components.sensor import SensorEntity

from homeassistant.core import (
    HomeAssistant,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from datetime import timedelta
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from homeassistant.components.recorder import DEFAULT_DB_FILE, DEFAULT_URL

from .const import (
    DOMAIN)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)

async def async_setup_entry(hass : HomeAssistant, config: ConfigType, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    
    hub = hass.data[DOMAIN]["hub"]
    
    devicesensor = []
    devicesensor.append(DeviceSensor(hub, "Peaq controller"))
    async_add_entities(devicesensor, update_before_add = True)

    peaqsensors = await gather_Sensors(hass, hub)
    async_add_entities(peaqsensors, update_before_add = True)

    peaqintegrationsensors = []
    peaqintegrationsensors.append(PeaqIntegrationSensor(hub, hub.powersensorentity, f"{ex.NameToId(hub.CONSUMPTION_INTEGRAL_NAME)}"))
    peaqintegrationsensors.append(PeaqIntegrationSensor(hub, f"sensor.{DOMAIN}_{ex.NameToId(hub.TotalPowerSensor.Name)}", f"{ex.NameToId(hub.CONSUMPTION_TOTAL_NAME)}"))
    async_add_entities(peaqintegrationsensors, update_before_add = True)

    integrationsensors = [ex.NameToId(hub.CONSUMPTION_TOTAL_NAME), ex.NameToId(hub.CONSUMPTION_INTEGRAL_NAME)]
    peaqutilitysensors = []

    for i in integrationsensors:
        for p in PERIODS:
            peaqutilitysensors.append(PeaqUtilitySensor(hub, i, p, METER_OFFSET))
    
    async_add_entities(peaqutilitysensors, update_before_add = True)

    #sql sensors
    peaqsqlsensors = []
    peaks = hub.LocaleData

    db_url = DEFAULT_URL.format(hass_config_path=hass.config.path(DEFAULT_DB_FILE))
    engine = sqlalchemy.create_engine(db_url)
    sessmaker = scoped_session(sessionmaker(bind=engine))
    sqlsensor = hub.TotalHourlyEnergy_Entity
    sql = PeaqSQLSensorHelper(sqlsensor).GetQueryType(peaks.ChargedPeak)
    peaqsqlsensors.append(PeaqSQLSensor(hub, sessmaker, sql))

    if peaks.ChargedPeak != peaks.ObservedPeak:
        sql2 = PeaqSQLSensorHelper(sqlsensor).GetQueryType(peaks.ObservedPeak)
        peaqsqlsensors.append(PeaqSQLSensor(hub, sessmaker, sql2))
    #sql sensors
    
    async_add_entities(peaqsqlsensors, update_before_add = True)

async def gather_Sensors(hass: HomeAssistant, hub) -> list:
    peaqsensors = []
    peaqsensors.append(PeaqPowerSensor(hub, hass))
    peaqsensors.append(PeaqAmpSensor(hub, hass))
    peaqsensors.append(PeaqAverageSensor(hub))
    peaqsensors.append(PeaqPredictionSensor(hub)) #predictions
    peaqsensors.append(PeaqThresholdSensor(hub)) #thresholds
    peaqsensors.append(PeaqSensor(hub)) #chargecontroller
    return peaqsensors
    
class DeviceSensor(SensorEntity):
    should_poll = True

    def __init__(self, hub, name):
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = f"{self._hub.HUB_ID}_wrapper"
        self._attr_available = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._hub.HUB_ID)},
            "name": self._attr_name,
            "sw_version": 1,
            "model": f"{self._hub.LocaleData.Type} ({self._hub.ChargerTypeData.Type})",
            "manufacturer": "Peaq systems",
        }