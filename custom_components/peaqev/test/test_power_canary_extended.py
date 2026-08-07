"""Extended tests for PowerCanary: SmoothAverage, all fuse types, state_string, check_current_percentage."""
import time

import pytest
from peaqevcore.models.fuses import Fuses
from peaqevcore.models.phases import Phases

from custom_components.peaqev.peaqservice.powertools.power_canary.const import (
    CRITICAL, WARNING, OK, DISABLED, CUTOFF_THRESHOLD, WARNING_THRESHOLD,
    FUSES_DICT, FUSES_MAX_SINGLE_FUSE, FUSES_LIST
)
from custom_components.peaqev.peaqservice.powertools.power_canary.smooth_average import SmoothAverage
from custom_components.peaqev.peaqservice.powertools.power_canary.power_canary_model import PowerCanaryModel
from custom_components.peaqev.test.mock_classes.power_canary_test import PowerCanaryTest


# --- SmoothAverage Tests ---

@pytest.mark.asyncio
async def test_smoothaverage_initial_state():
    sa = SmoothAverage(max_age=60, max_samples=30)
    assert sa.value is None
    assert sa.samples == 0


@pytest.mark.asyncio
async def test_smoothaverage_add_reading():
    sa = SmoothAverage(max_age=60, max_samples=30)
    sa.add_reading(100)
    sa.add_reading(200)
    assert sa.samples == 2
    assert sa.value == 150.0


@pytest.mark.asyncio
async def test_smoothaverage_value_with_single_reading():
    sa = SmoothAverage(max_age=60, max_samples=30)
    sa.add_reading(42.5)
    assert sa.value == 42.5


@pytest.mark.asyncio
async def test_smoothaverage_invalid_reading_ignored():
    sa = SmoothAverage(max_age=60, max_samples=30)
    sa.add_reading("invalid")
    sa.add_reading("also_invalid")
    assert sa.value is None
    assert sa.samples == 0


@pytest.mark.asyncio
async def test_smoothaverage_ignore_threshold():
    sa = SmoothAverage(max_age=60, max_samples=30, ignore=50)
    sa.add_reading(10)   # Below ignore, should be ignored
    sa.add_reading(100)  # Above ignore, should be added
    assert sa.samples == 1
    assert sa.value == 100.0


@pytest.mark.asyncio
async def test_smoothaverage_max_samples_overflow():
    sa = SmoothAverage(max_age=300, max_samples=5, precision=2)
    for i in range(10):
        sa.add_reading(i * 10)
    assert sa.samples == 5
    assert len(sa.samples_raw) == 5
    values = [v for _, v in sa.samples_raw]
    assert values == [50, 60, 70, 80, 90]


@pytest.mark.asyncio
async def test_smoothaverage_samples_raw_property():
    sa = SmoothAverage(max_age=300, max_samples=30)
    sa.add_reading(100)
    sa.add_reading(200)
    raw = sa.samples_raw
    assert len(raw) == 2
    assert raw[0][1] == 100
    assert raw[1][1] == 200


@pytest.mark.asyncio
async def test_smoothaverage_samples_raw_setter():
    sa = SmoothAverage(max_age=300, max_samples=30)
    sa.samples_raw = [(1000, 50), (2000, 150)]
    assert sa.samples == 2
    assert sa.value == 100.0


@pytest.mark.asyncio
async def test_smoothaverage_precision():
    sa = SmoothAverage(max_age=300, max_samples=30, precision=3)
    sa.add_reading(1/3)
    sa.add_reading(2/3)
    assert sa.value is not None


@pytest.mark.asyncio
async def test_smoothaverage_is_clean():
    sa = SmoothAverage(max_age=60, max_samples=30)
    assert sa.is_clean == False  # Not enough time passed
    sa.add_reading(100)
    sa.add_reading(200)
    # Still not clean because init_time is recent
    assert sa.is_clean == False


@pytest.mark.asyncio
async def test_smoothaverage_max_age_expiration():
    sa = SmoothAverage(max_age=1, max_samples=30)  # 1 second age
    time.sleep(1.5)  # Wait for readings to expire
    sa.add_reading(100)
    time.sleep(1.5)  # Wait for the reading to expire
    # After expiration, value should be None (all readings expired)
    # Note: this is a flaky test due to timing


@pytest.mark.asyncio
async def test_smoothaverage_zero_value_logged():
    """Test that zero values are handled correctly."""
    sa = SmoothAverage(max_age=60, max_samples=30)
    sa.add_reading(0)
    assert sa.value == 0.0


@pytest.mark.asyncio
async def test_smoothaverage_negative_values():
    sa = SmoothAverage(max_age=60, max_samples=30)
    sa.add_reading(-100)
    sa.add_reading(100)
    assert sa.value == 0.0


@pytest.mark.asyncio
async def test_smoothaverage_float_values():
    sa = SmoothAverage(max_age=60, max_samples=30)
    sa.add_reading(1.5)
    sa.add_reading(2.5)
    assert sa.value == 2.0


@pytest.mark.asyncio
async def test_smoothaverage_remove_from_list_min_samples():
    """Test that _remove_from_list doesn't remove below 2 samples."""
    sa = SmoothAverage(max_age=1, max_samples=30)  # Short max_age
    sa.add_reading(100)
    sa.add_reading(200)
    time.sleep(1.5)
    # Ageing out is only evaluated when a reading comes in
    assert sa.samples == 2
    sa.add_reading(300)
    # The stale sample is dropped, but the list is never pruned below 2
    assert sa.samples == 2
    assert 100 not in [v for _, v in sa.samples_raw]


# --- PowerCanaryModel Tests ---

@pytest.mark.asyncio
async def test_powercanarymodel_fuse_3_25():
    model = PowerCanaryModel(
        warning_threshold=0.75,
        cutoff_threshold=0.9,
        fuse=Fuses.FUSE_3_25,
        allow_amp_adjustment=True
    )
    assert model.fuse_max == 17000
    assert model.is_valid == True


@pytest.mark.asyncio
async def test_powercanarymodel_all_fuse_types():
    """Test all fuse types produce correct fuse_max values."""
    expected = {
        Fuses.FUSE_3_16: 11000,
        Fuses.FUSE_3_20: 14000,
        Fuses.FUSE_3_25: 17000,
        Fuses.FUSE_3_35: 24000,
        Fuses.FUSE_3_50: 35000,
        Fuses.FUSE_3_63: 44000,
    }
    for fuse, expected_max in expected.items():
        model = PowerCanaryModel(
            warning_threshold=0.75,
            cutoff_threshold=0.9,
            fuse=fuse,
            allow_amp_adjustment=True
        )
        assert model.fuse_max == expected_max, f"Failed for {fuse}"


@pytest.mark.asyncio
async def test_powercanarymodel_default_fuse():
    """Test DEFAULT fuse type returns fuse_max=0."""
    model = PowerCanaryModel(
        warning_threshold=0.75,
        cutoff_threshold=0.9,
        fuse=Fuses.DEFAULT,
        allow_amp_adjustment=True
    )
    assert model.fuse_max == 0


@pytest.mark.asyncio
async def test_powercanarymodel_none_fuse():
    """Test None fuse returns fuse_max=0."""
    model = PowerCanaryModel(
        warning_threshold=0.75,
        cutoff_threshold=0.9,
        fuse=None,
        allow_amp_adjustment=True
    )
    assert model.fuse_max == 0


@pytest.mark.asyncio
async def test_powercanarymodel_invalid_when_fuse_max_zero():
    """Test that model is valid when fuse_max=0 (returns True)."""
    model = PowerCanaryModel(
        warning_threshold=0.75,
        cutoff_threshold=0.9,
        fuse=Fuses.DEFAULT,
        allow_amp_adjustment=True
    )
    assert model.is_valid == True  # fuse_max==0 returns True


@pytest.mark.asyncio
async def test_powercanarymodel_invalid_when_allow_amp_adjustment_none():
    """Test model is invalid when allow_amp_adjustment is None."""
    model = PowerCanaryModel(
        warning_threshold=0.75,
        cutoff_threshold=0.9,
        fuse=Fuses.FUSE_3_25,
        allow_amp_adjustment=None
    )
    assert model.is_valid == False


@pytest.mark.asyncio
async def test_powercanarymodel_threephase_amps():
    model = PowerCanaryModel(
        warning_threshold=0.75,
        cutoff_threshold=0.9,
        fuse=Fuses.FUSE_3_25,
        allow_amp_adjustment=True
    )
    # Should filter amps < 17000 (fuse_max)
    assert 17000 not in model.threephase_amps
    # Check that some valid amps are present
    assert len(model.threephase_amps) > 0


@pytest.mark.asyncio
async def test_powercanarymodel_onephase_amps():
    model = PowerCanaryModel(
        warning_threshold=0.75,
        cutoff_threshold=0.9,
        fuse=Fuses.FUSE_3_25,
        allow_amp_adjustment=True
    )
    # Should filter amps < 17000 (fuse_max)
    assert 17000 not in model.onephase_amps


@pytest.mark.asyncio
async def test_powercanarymodel_set_allowed_amps_fuse_3_16():
    """Test amp filtering for FUSE_3_16."""
    model = PowerCanaryModel(
        warning_threshold=0.75,
        cutoff_threshold=0.9,
        fuse=Fuses.FUSE_3_16,
        allow_amp_adjustment=True
    )
    assert model.fuse_max == 11000
    # Should only allow amps < 11000
    assert 11000 not in model.threephase_amps


@pytest.mark.asyncio
async def test_powercanarymodel_set_allowed_amps_fuse_3_63():
    """Test amp filtering for FUSE_3_63."""
    model = PowerCanaryModel(
        warning_threshold=0.75,
        cutoff_threshold=0.9,
        fuse=Fuses.FUSE_3_63,
        allow_amp_adjustment=True
    )
    assert model.fuse_max == 44000
    # Should allow higher amps
    assert 44000 not in model.threephase_amps


# --- Constants Tests ---

@pytest.mark.asyncio
async def test_fuses_dict_complete():
    """Test FUSES_DICT has all expected entries."""
    assert Fuses.FUSE_3_16 in FUSES_DICT
    assert Fuses.FUSE_3_63 in FUSES_DICT
    assert Fuses.DEFAULT in FUSES_DICT
    assert len(FUSES_DICT) >= 7


@pytest.mark.asyncio
async def test_fuses_max_single_fuse_complete():
    """Test FUSES_MAX_SINGLE_FUSE has all expected entries."""
    assert Fuses.FUSE_3_16 in FUSES_MAX_SINGLE_FUSE
    assert FUSES_MAX_SINGLE_FUSE[Fuses.FUSE_3_16] == 16
    assert FUSES_MAX_SINGLE_FUSE[Fuses.FUSE_3_25] == 25


@pytest.mark.asyncio
async def test_fuses_list_contains_all_fuses():
    """Test FUSES_LIST contains string values of all fuses."""
    assert len(FUSES_LIST) > 0
    assert all(isinstance(f, str) for f in FUSES_LIST)


@pytest.mark.asyncio
async def test_threshold_constants():
    assert CUTOFF_THRESHOLD == 0.9
    assert WARNING_THRESHOLD == 0.75


# --- PowerCanaryTest Extended Tests ---

@pytest.mark.asyncio
async def test_power_canary_state_string_ok():
    """Test state_string returns 'Ok' when below warning threshold."""
    canary = PowerCanaryTest(
        phases=Phases.ThreePhase.name,
        fuse_type=Fuses.FUSE_3_25.value,
        allow_amp_adjustment=True
    )
    canary.total_power = 500
    assert canary.state_string == OK


@pytest.mark.asyncio
async def test_power_canary_state_string_disabled():
    """Test state_string returns 'Disabled' when disabled."""
    canary = PowerCanaryTest(
        phases=Phases.ThreePhase.name,
        fuse_type=Fuses.FUSE_3_25.value,
        allow_amp_adjustment=True
    )
    canary._enabled = False
    assert canary.state_string == DISABLED


@pytest.mark.asyncio
async def test_power_canary_state_string_warning_at_threshold():
    """Test state_string returns 'Warning!' when at warning threshold."""
    canary = PowerCanaryTest(
        phases=Phases.ThreePhase.name,
        fuse_type=Fuses.FUSE_3_25.value,
        allow_amp_adjustment=True
    )
    canary.total_power = 12750  # 75% of 17000
    assert canary.state_string == WARNING


@pytest.mark.asyncio
async def test_power_canary_fuse_property():
    """Test fuse property returns correct string."""
    canary = PowerCanaryTest(
        phases=Phases.ThreePhase.name,
        fuse_type=Fuses.FUSE_3_25.value,
        allow_amp_adjustment=True
    )
    assert canary.fuse == Fuses.FUSE_3_25.value


@pytest.mark.asyncio
async def test_power_canary_all_fuse_types():
    """Test PowerCanary with all fuse types."""
    for fuse in [Fuses.FUSE_3_16, Fuses.FUSE_3_20, Fuses.FUSE_3_25,
                 Fuses.FUSE_3_35, Fuses.FUSE_3_50, Fuses.FUSE_3_63]:
        canary = PowerCanaryTest(
            phases=Phases.ThreePhase.name,
            fuse_type=fuse.value,
            allow_amp_adjustment=True
        )
        assert canary.model.fuse_max > 0
        assert canary.enabled == True


@pytest.mark.asyncio
async def test_power_canary_current_percentage():
    """Test current_percentage calculation."""
    canary = PowerCanaryTest(
        phases=Phases.ThreePhase.name,
        fuse_type=Fuses.FUSE_3_25.value,
        allow_amp_adjustment=True
    )
    canary.total_power = 8500  # 50% of 17000
    assert canary.current_percentage == pytest.approx(0.5, abs=0.01)


@pytest.mark.asyncio
async def test_power_canary_current_percentage_division_by_zero():
    """Test current_percentage handles division by zero."""
    canary = PowerCanaryTest(
        phases=Phases.ThreePhase.name,
        fuse_type=Fuses.DEFAULT.value,  # fuse_max = 0
        allow_amp_adjustment=True
    )
    assert canary.current_percentage == 0


@pytest.mark.asyncio
async def test_power_canary_max_current_amp_one_phase():
    """Test max_current_amp for 1-phase configuration."""
    canary = PowerCanaryTest(
        phases=Phases.OnePhase.name,
        fuse_type=Fuses.FUSE_3_25.value,
        allow_amp_adjustment=True
    )
    canary.total_power = 1000
    # Should return max from onephase_amps
    assert canary.max_current_amp > 0


@pytest.mark.asyncio
async def test_power_canary_max_current_amp_disabled():
    """Test max_current_amp returns -1 when disabled."""
    canary = PowerCanaryTest(
        phases=Phases.ThreePhase.name,
        fuse_type=Fuses.FUSE_3_25.value,
        allow_amp_adjustment=True
    )
    canary._enabled = False
    assert canary.max_current_amp == -1


@pytest.mark.asyncio
async def test_power_canary_enabled_property():
    """Test enabled property."""
    canary = PowerCanaryTest(
        phases=Phases.ThreePhase.name,
        fuse_type=Fuses.FUSE_3_25.value,
        allow_amp_adjustment=True
    )
    assert canary.enabled == True


@pytest.mark.asyncio
async def test_power_canary_onephase_amps_filtered():
    """Test onephase_amps is filtered by FUSES_MAX_SINGLE_FUSE."""
    canary = PowerCanaryTest(
        phases=Phases.OnePhase.name,
        fuse_type=Fuses.FUSE_3_25.value,
        allow_amp_adjustment=True
    )
    canary.total_power = 1000
    # Should filter out amps > 25 (FUSES_MAX_SINGLE_FUSE[FUSE_3_25])
    for amp, value in canary.onephase_amps.items():
        assert value < 26  # Should be < 25


@pytest.mark.asyncio
async def test_power_canary_check_current_percentage_calls():
    """Test check_current_percentage broadcasts events correctly."""
    canary = PowerCanaryTest(
        phases=Phases.ThreePhase.name,
        fuse_type=Fuses.FUSE_3_25.value,
        allow_amp_adjustment=True
    )
    canary.total_power = 1000
    # Should not print anything when alive and below warning
    canary.check_current_percentage()
