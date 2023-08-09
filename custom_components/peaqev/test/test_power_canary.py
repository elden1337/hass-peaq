import pytest
from peaqevcore.models.fuses import Fuses
from peaqevcore.models.phases import Phases

from custom_components.peaqev.peaqservice.powertools.power_canary.const import (
    CRITICAL, WARNING)
from custom_components.peaqev.peaqservice.powertools.power_canary.power_canary_test import \
    PowerCanaryTest


@pytest.mark.asyncio
async def test_power_canary():
    canary = PowerCanaryTest(phases=Phases.ThreePhase.name, fuse_type=Fuses.FUSE_3_25.value, allow_amp_adjustment=True)
    canary.total_power = 1000
    assert canary.model.is_valid
    assert canary.alive == True
    assert canary.max_current_amp == 16
    assert canary.threephase_amps == {4100: 6, 5500: 8, 6875: 10, 8250: 12, 9625: 14, 11000: 16}


@pytest.mark.asyncio
async def test_power_canary_warning():
    canary = PowerCanaryTest(phases=Phases.ThreePhase.name, fuse_type=Fuses.FUSE_3_25.value, allow_amp_adjustment=True)
    canary.total_power = 1000
    assert canary.alive == True
    canary.total_power = 25000
    assert canary.alive == True
    assert canary.state_string == WARNING


@pytest.mark.asyncio
async def test_power_canary_dead():
    canary = PowerCanaryTest(phases=Phases.ThreePhase.name, fuse_type=Fuses.FUSE_3_25.value, allow_amp_adjustment=True)
    canary.total_power = 1000
    assert canary.alive == True
    canary.total_power = 100000
    assert canary.alive == False
    assert canary.state_string == CRITICAL


@pytest.mark.asyncio
async def test_power_canary_allow_amps_adjustment_1():
    canary = PowerCanaryTest(phases=Phases.ThreePhase.name, fuse_type=Fuses.FUSE_3_25.value, allow_amp_adjustment=True)
    canary.total_power = 1000
    allow_check = await canary.async_allow_adjustment(new_amps=12)
    assert allow_check == True


@pytest.mark.asyncio
async def test_power_canary_allow_amps_adjustment_2():
    canary = PowerCanaryTest(phases=Phases.ThreePhase.name, fuse_type=Fuses.FUSE_3_16.value, allow_amp_adjustment=True)
    canary.total_power = 8000
    allow_check = await canary.async_allow_adjustment(new_amps=12)
    assert allow_check == False


@pytest.mark.asyncio
async def test_power_canary_allow_amps_adjustment_3():
    canary = PowerCanaryTest(phases=Phases.ThreePhase.name, fuse_type=Fuses.FUSE_3_25.value, allow_amp_adjustment=False)
    canary.total_power = 1000
    allow_check = await canary.async_allow_adjustment(new_amps=12)
    assert allow_check == False
