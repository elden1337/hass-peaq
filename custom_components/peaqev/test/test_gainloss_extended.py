"""Extended tests for GainLoss: async_state, error paths, invalid states, normalize_numbers."""
import pytest
from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.peaqservice.powertools.gainloss.const import (
    CONSUMPTION, COST, DAILY_COST_SENSOR, DAILY_ENERGY_SENSOR, INVALID_STATES,
    MONTHLY_COST_SENSOR, MONTHLY_ENERGY_SENSOR)
from custom_components.peaqev.peaqservice.powertools.gainloss.igain_loss import \
    IGainLoss
from custom_components.peaqev.test.conftest import MockGainLoss

# --- async_state Tests ---

@pytest.mark.asyncio
async def test_gainloss_async_state_not_initialized():
    """Test async_state returns 0.0 when not initialized."""
    gainloss = MockGainLoss()
    result = await gainloss.async_state(TimePeriods.Daily)
    assert result == 0.0


@pytest.mark.asyncio
async def test_gainloss_async_state_initialized():
    """Test async_state when initialized with valid data."""
    gainloss = MockGainLoss({
        DAILY_ENERGY_SENSOR: 10.0,
        DAILY_COST_SENSOR: 2.0
    })
    gainloss._daily_average = 0.3
    gainloss._monthly_average = 0.5
    result = await gainloss.async_state(TimePeriods.Daily)
    assert result is not None


@pytest.mark.asyncio
async def test_gainloss_async_state_monthly():
    """Test async_state with monthly time period."""
    gainloss = MockGainLoss({
        MONTHLY_ENERGY_SENSOR: 100.0,
        MONTHLY_COST_SENSOR: 20.0
    })
    gainloss._daily_average = 0.3
    gainloss._monthly_average = 0.5
    result = await gainloss.async_state(TimePeriods.Monthly)
    assert result is not None


# --- is_initialized Tests ---

@pytest.mark.asyncio
async def test_gainloss_is_initialized_false():
    """Test is_initialized returns False when averages are None."""
    gainloss = MockGainLoss()
    assert gainloss.is_initialized == False


@pytest.mark.asyncio
async def test_gainloss_is_initialized_true():
    """Test is_initialized returns True when both averages are set."""
    gainloss = MockGainLoss()
    gainloss._daily_average = 0.3
    gainloss._monthly_average = 0.5
    assert gainloss.is_initialized == True


@pytest.mark.asyncio
async def test_gainloss_is_initialized_partial():
    """Test is_initialized returns False when only one average is set."""
    gainloss = MockGainLoss()
    gainloss._daily_average = 0.3
    assert gainloss.is_initialized == False


# --- async_calculate_state Error Paths ---

@pytest.mark.asyncio
async def test_gainloss_calculate_state_typeerror():
    """Test async_calculate_state handles TypeError in normalize_numbers."""
    gainloss = MockGainLoss()
    # When normalize_numbers raises TypeError, should return 0.0
    result = await gainloss.async_calculate_state("invalid", "also_invalid", TimePeriods.Daily)
    assert result == 0.0


@pytest.mark.asyncio
async def test_gainloss_calculate_state_zerodivision():
    """Test async_calculate_state handles ZeroDivisionError."""
    gainloss = MockGainLoss({
        DAILY_ENERGY_SENSOR: 0.0,
        DAILY_COST_SENSOR: 0.0
    })
    gainloss._daily_average = 0.3
    gainloss._monthly_average = 0.5
    result = await gainloss.async_calculate_state(0.0, 0.0, TimePeriods.Daily)
    assert result == 0.0


@pytest.mark.asyncio
async def test_gainloss_check_invalid_states_unknown():
    """Test async_check_invalid_states with 'unknown' string."""
    result = await IGainLoss.async_check_invalid_states("unknown", 1.0)
    assert result == True


@pytest.mark.asyncio
async def test_gainloss_check_invalid_states_unavailable():
    """Test async_check_invalid_states with 'unavailable' string."""
    result = await IGainLoss.async_check_invalid_states(1.0, "unavailable")
    assert result == True


@pytest.mark.asyncio
async def test_gainloss_check_invalid_states_invalid_list():
    """Test that INVALID_STATES contains expected values."""
    assert "unknown" in INVALID_STATES
    assert "unavailable" in INVALID_STATES


@pytest.mark.asyncio
async def test_gainloss_check_invalid_states_valid_values():
    """Test async_check_invalid_states with valid numeric values."""
    result = await IGainLoss.async_check_invalid_states(100.0, 20.0)
    assert result == False


# --- normalize_numbers Tests ---

@pytest.mark.asyncio
async def test_normalize_numbers_normal_case():
    """Test normalize_numbers with normal positive values."""
    avg, cost = IGainLoss.normalize_numbers(0.5, 0.3)
    assert avg == 0.5
    assert cost == 0.3


@pytest.mark.asyncio
async def test_normalize_numbers_negative_values():
    """Test normalize_numbers with negative values."""
    avg, cost = IGainLoss.normalize_numbers(-0.5, -0.3)
    # Should add diff and adjust both
    assert avg > 0 or cost > 0


@pytest.mark.asyncio
async def test_normalize_numbers_mixed_signs():
    """Test normalize_numbers with mixed positive/negative."""
    avg, cost = IGainLoss.normalize_numbers(-0.5, 0.3)
    # Should handle mixed signs


@pytest.mark.asyncio
async def test_normalize_numbers_typeerror():
    """Test normalize_numbers TypeError path."""
    avg, cost = IGainLoss.normalize_numbers(None, "invalid")
    # Should return as-is when TypeError occurs
    assert avg is None and cost == "invalid"


@pytest.mark.asyncio
async def test_normalize_numbers_rounding():
    """Test normalize_numbers rounds to 3 decimal places."""
    avg, cost = IGainLoss.normalize_numbers(0.123456, 0.789456)
    assert avg == 0.123
    assert cost == 0.789


# --- async_get_average Tests ---

@pytest.mark.asyncio
async def test_gainloss_get_average_monthly():
    """Test async_get_average with Monthly time period."""
    gainloss = MockGainLoss()
    gainloss._monthly_average = 0.5
    result = await gainloss.async_get_average(TimePeriods.Monthly)
    assert result == 0.5


@pytest.mark.asyncio
async def test_gainloss_get_average_daily():
    """Test async_get_average with Daily time period."""
    gainloss = MockGainLoss()
    gainloss._daily_average = 0.3
    result = await gainloss.async_get_average(TimePeriods.Daily)
    assert result == 0.3


@pytest.mark.asyncio
async def test_gainloss_get_average_invalid():
    """Test async_get_average with invalid time period raises ValueError."""
    gainloss = MockGainLoss()
    with pytest.raises(ValueError):
        await gainloss.async_get_average("InvalidPeriod")


# --- async_get_entity Tests ---

@pytest.mark.asyncio
async def test_gainloss_get_entity_daily_consumption():
    """Test async_get_entity for daily consumption."""
    result = await IGainLoss.async_get_entity(TimePeriods.Daily, CONSUMPTION)
    assert result == DAILY_ENERGY_SENSOR


@pytest.mark.asyncio
async def test_gainloss_get_entity_daily_cost():
    """Test async_get_entity for daily cost."""
    result = await IGainLoss.async_get_entity(TimePeriods.Daily, COST)
    assert result == DAILY_COST_SENSOR


@pytest.mark.asyncio
async def test_gainloss_get_entity_monthly_consumption():
    """Test async_get_entity for monthly consumption."""
    result = await IGainLoss.async_get_entity(TimePeriods.Monthly, CONSUMPTION)
    assert result == MONTHLY_ENERGY_SENSOR


@pytest.mark.asyncio
async def test_gainloss_get_entity_monthly_cost():
    """Test async_get_entity for monthly cost."""
    result = await IGainLoss.async_get_entity(TimePeriods.Monthly, COST)
    assert result == MONTHLY_COST_SENSOR


# --- Edge Cases ---

@pytest.mark.asyncio
async def test_gainloss_calculate_state_both_negative_clamped():
    """Test result clamping to [-1.0, 1.0] when both consumption and cost are negative."""
    gainloss = MockGainLoss({
        DAILY_ENERGY_SENSOR: 50.0,
        DAILY_COST_SENSOR: -5.0
    })
    gainloss._daily_average = -0.01
    result = await gainloss.async_calculate_state(50.0, -5.0, TimePeriods.Daily)
    assert -1.0 <= result <= 1.0


@pytest.mark.asyncio
async def test_gainloss_calculate_state_very_large_values():
    """Test with very large consumption/cost values."""
    gainloss = MockGainLoss({
        DAILY_ENERGY_SENSOR: 1000000.0,
        DAILY_COST_SENSOR: 200000.0
    })
    gainloss._daily_average = 0.3
    result = await gainloss.async_calculate_state(1000000.0, 200000.0, TimePeriods.Daily)
    assert -1.0 <= result <= 1.0


@pytest.mark.asyncio
async def test_gainloss_calculate_state_very_small_values():
    """Test with very small consumption/cost values."""
    gainloss = MockGainLoss({
        DAILY_ENERGY_SENSOR: 0.001,
        DAILY_COST_SENSOR: 0.0001
    })
    gainloss._daily_average = 0.0003
    result = await gainloss.async_calculate_state(0.001, 0.0001, TimePeriods.Daily)
    assert -1.0 <= result <= 1.0


@pytest.mark.asyncio
async def test_gainloss_update_monthly_average():
    """Test _update_monthly_average sets value."""
    gainloss = MockGainLoss()
    gainloss._update_monthly_average(0.75)
    assert gainloss._monthly_average == 0.75


@pytest.mark.asyncio
async def test_gainloss_update_daily_average():
    """Test _update_daily_average sets value."""
    gainloss = MockGainLoss()
    gainloss._update_daily_average(0.25)
    assert gainloss._daily_average == 0.25


@pytest.mark.asyncio
async def test_gainloss_async_state_attribute_error():
    """Test async_state handles AttributeError from async_get_consumption."""
    gainloss = MockGainLoss({})
    gainloss._daily_average = 0.3
    gainloss._monthly_average = 0.5
    result = await gainloss.async_state(TimePeriods.Daily)
    assert result == 0.0
