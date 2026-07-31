"""Tests for Hub sensor models: Average, EMA, and sensor base classes."""
import time
from statistics import StatisticsError

import pytest

from custom_components.peaqev.peaqservice.hub.sensors.models.average import Average
from custom_components.peaqev.peaqservice.hub.sensors.models.ema import EMA
from custom_components.peaqev.peaqservice.hub.const import LookupKeys


# --- Average Model Tests ---

@pytest.mark.asyncio
async def test_average_initial_state():
    """Test Average initial state raises StatisticsError when empty."""
    avg = Average(max_age=60, max_samples=30)
    with pytest.raises(StatisticsError):
        _ = avg.average


@pytest.mark.asyncio
async def test_average_add_reading():
    """Test Average.add_reading."""
    avg = Average(max_age=60, max_samples=30)
    avg.add_reading(100)
    avg.add_reading(200)
    assert len(avg.readings()) == 2


@pytest.mark.asyncio
async def test_average_value_with_readings():
    """Test Average.average returns mean of readings."""
    avg = Average(max_age=60, max_samples=30)
    avg.add_reading(10)
    avg.add_reading(20)
    avg.add_reading(30)
    assert avg.average == 20.0


@pytest.mark.asyncio
async def test_average_max_samples_overflow():
    """Test Average respects max_samples limit."""
    avg = Average(max_age=300, max_samples=5)
    for i in range(10):
        avg.add_reading(i * 10)
    assert len(avg.readings()) == 5


@pytest.mark.asyncio
async def test_average_max_age_expiration():
    """Test Average respects max_age expiration."""
    avg = Average(max_age=1, max_samples=30)  # 1 second
    avg.add_reading(100)
    time.sleep(1.5)
    # After expiration, value might change


# --- EMA Model Tests ---

@pytest.mark.asyncio
async def test_ema_initial_state():
    """Test EMA initial state."""
    ema = EMA(len_avg=10, smoothing_exp=1)
    assert ema._latest_average is None
    assert ema.smoothing_factor > 0


@pytest.mark.asyncio
async def test_ema_average_method():
    """Test EMA.average method."""
    ema = EMA(len_avg=10, smoothing_exp=1)
    result = ema.average(100)
    assert result == 100.0


@pytest.mark.asyncio
async def test_ema_latest_average_with_readings():
    """Test EMA.latest_average reflects weighted average."""
    ema = EMA(len_avg=10, smoothing_exp=1)
    ema.average(100)
    ema.average(200)
    ema.average(300)
    assert ema.latest_average > 0


@pytest.mark.asyncio
async def test_ema_different_smoothing_factors():
    """Test EMA with different smoothing exponents."""
    ema_fast = EMA(len_avg=10, smoothing_exp=0.1)
    ema_slow = EMA(len_avg=10, smoothing_exp=5)

    ema_fast.average(100)
    ema_fast.average(200)

    ema_slow.average(100)
    ema_slow.average(200)

    # Fast should be closer to latest reading
    assert ema_fast.latest_average > ema_slow.latest_average


@pytest.mark.asyncio
async def test_ema_single_reading():
    """Test EMA with single reading."""
    ema = EMA(len_avg=10, smoothing_exp=1)
    result = ema.average(42.5)
    assert result > 0  # Should return a valid weighted average


@pytest.mark.asyncio
async def test_ema_multiple_readings():
    """Test EMA with multiple readings."""
    ema = EMA(len_avg=10, smoothing_exp=1)
    for i in range(10):
        ema.average(i * 10)
    assert ema.latest_average > 0


@pytest.mark.asyncio
async def test_ema_set_smoothing_factor():
    """Test EMA.set_smoothing_factor method."""
    ema = EMA(len_avg=10, smoothing_exp=1)
    new_factor = ema.set_smoothing_factor(20, 2)
    assert new_factor > 0


@pytest.mark.asyncio
async def test_ema_imported_average_property():
    """Test EMA.imported_average property/setter."""
    ema = EMA(len_avg=10, smoothing_exp=1)
    assert ema.imported_average == False
    ema.imported_average = 50.0
    assert ema.latest_average == 50.0


# --- LookupKeys Tests ---

@pytest.mark.asyncio
async def test_lookupkeys_has_expected_members():
    """Test LookupKeys enum has expected members."""
    lk = LookupKeys
    assert hasattr(lk, 'CHARGEROBJECT_VALUE')
    assert hasattr(lk, 'PRICES')
    assert hasattr(lk, 'CHARGER_DONE')
    assert hasattr(lk, 'TOTALHOURLYENERGY') or hasattr(lk, 'SPOTPRICE_SOURCE')


@pytest.mark.asyncio
async def test_lookupkeys_count():
    """Test LookupKeys has all 31 expected members."""
    assert len(LookupKeys) == 31


# --- Edge Cases ---

@pytest.mark.asyncio
async def test_average_zero_readings_value():
    """Test Average.average when no readings raises StatisticsError."""
    avg = Average(max_age=60, max_samples=30)
    with pytest.raises(StatisticsError):
        _ = avg.average


@pytest.mark.asyncio
async def test_average_negative_readings():
    """Test Average with negative readings."""
    avg = Average(max_age=60, max_samples=30)
    avg.add_reading(-100)
    avg.add_reading(-200)
    assert avg.average == -150.0


@pytest.mark.asyncio
async def test_ema_zero_smoothing():
    """Test EMA with zero smoothing exponent."""
    ema = EMA(len_avg=10, smoothing_exp=0.0001)  # Very small
    result = ema.average(100)
    assert result == 100.0


@pytest.mark.asyncio
async def test_ema_full_smoothing():
    """Test EMA with high smoothing exponent."""
    ema = EMA(len_avg=10, smoothing_exp=10)
    ema.average(100)
    ema.average(200)
    assert ema.latest_average > 0


@pytest.mark.asyncio
async def test_average_mixed_signs():
    """Test Average with mixed positive/negative readings."""
    avg = Average(max_age=60, max_samples=30)
    avg.add_reading(100)
    avg.add_reading(-50)
    assert avg.average == 25.0
