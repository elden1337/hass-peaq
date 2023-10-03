from enum import Enum


class ObserverTypes(Enum):
    Test = "test"
    HubInitialized = "hub initialized" #1
    SpotpriceInitialized = "spotprice initialized"

    PowerCanaryDead = "power canary dead"
    PowerCanaryWarning = "power canary warning"

    PricesChanged = "prices changed"
    MonthlyAveragePriceChanged = "monthly average price changed"
    AdjustedAveragePriceChanged = "adjusted average price changed"
    DailyAveragePriceChanged = "daily average price changed"
    DynamicMaxPriceChanged = "dynamic max price changed"

    CarConnected = "car connected"
    CarDisconnected = "car disconnected" #can this be combined with CarConnected and a bool clause instead?
    CarDone = "car done"

    UpdateChargerEnabled = "update charger enabled"
    UpdateChargerDone ="update charger done" #is this the same as CarDone?
    UpdateLatestChargerStart = "update latest charger start"

    AuxStopChanged = "aux stop changed"
    MaxMinLimiterChanged = "max min limiter changed"
    TimerActivated = "timer activated"
    SchedulerCreated = "scheduler created"
    SchedulerCancelled = "scheduler cancelled"
    KillswitchDead = "killswitch dead"

    ProcessChargeController = "process charge controller"
    ProcessCharger = "process charger"

    ResetMaxMinChargeSensor = "reset max min charge sensor"
    UpdatePeak = "update peak"