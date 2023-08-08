import pytest
from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.peaqservice.powertools.gainloss.const import *
from custom_components.peaqev.peaqservice.powertools.gainloss.gain_loss import GainLoss


@pytest.mark.asyncio
async def test_gainloss_correct_sensors():
    gainloss = GainLoss(test=True)
    assert await gainloss.async_get_entity(TimePeriods.Daily, CONSUMPTION) == DAILY_ENERGY_SENSOR
    assert await gainloss.async_get_entity(TimePeriods.Daily, COST) == DAILY_COST_SENSOR
    assert await gainloss.async_get_entity(TimePeriods.Monthly, CONSUMPTION) == MONTHLY_ENERGY_SENSOR
    assert await gainloss.async_get_entity(TimePeriods.Monthly, COST) == MONTHLY_COST_SENSOR

@pytest.mark.asyncio
async def test_gainloss_calculate_state_none_none():
    gainloss = GainLoss(test=True)
    assert await gainloss.async_calculate_state(None, None, TimePeriods.Daily) == 0.0

@pytest.mark.asyncio
async def test_gainloss_calculate_state_none_1():
    gainloss = GainLoss(test=True)
    assert await gainloss.async_calculate_state(None,1, TimePeriods.Daily) == 0.0

@pytest.mark.asyncio
async def test_gainloss_calculate_state_1_none():
    gainloss = GainLoss(test=True)
    assert await gainloss.async_calculate_state(1,None, TimePeriods.Daily) == 0.0

@pytest.mark.asyncio
async def test_gainloss_calculate_state_3():
    gainloss = GainLoss(test=True)
    gainloss._update_monthly_average(0.5)
    gainloss._update_daily_average(0.3)
    assert await gainloss.async_calculate_state(1,0.2, TimePeriods.Daily) == -0.3333

@pytest.mark.asyncio
async def test_gainloss_calculate_state_negative_sum():
    gainloss = GainLoss(test=True)
    gainloss._update_daily_average(0.01)
    assert -1.0 < await gainloss.async_calculate_state(16.67,-0.12, TimePeriods.Daily) < 1.0

@pytest.mark.asyncio
async def test_gainloss_calculate_state_negative_average():
    gainloss = GainLoss(test=True)
    gainloss._update_daily_average(-0.01)
    assert -1.0 < await gainloss.async_calculate_state(16.67,0.12, TimePeriods.Daily) < 1.0

@pytest.mark.asyncio
async def test_gainloss_calculate_state_negative_sum_and_average():
    gainloss = GainLoss(test=True)
    #gainloss._update_monthly_average(0.293625)
    gainloss._update_daily_average(-0.01)
    assert -1.0 < await gainloss.async_calculate_state(16.67,-0.12, TimePeriods.Daily) < 1.0
