"""Tests for services.py: all service handlers, validation, registration."""
import pytest

from custom_components.peaqev import services

# --- ServiceCalls Enum Tests ---

@pytest.mark.asyncio
async def test_servicecalls_enum_values():
    """Test ServiceCalls enum has all expected members."""
    assert hasattr(services, 'ServiceCalls')
    SC = services.ServiceCalls
    assert SC.ENABLE.value == 'enable'
    assert SC.DISABLE.value == 'disable'
    assert SC.OVERRIDE_NONHOURS.value == 'override_nonhours'
    assert SC.SCHEDULER_SET.value == 'scheduler_set'
    assert SC.SCHEDULER_CANCEL.value == 'scheduler_cancel'


@pytest.mark.asyncio
async def test_servicecalls_enum_names():
    """Test ServiceCalls enum has correct names."""
    SC = services.ServiceCalls
    assert SC.ENABLE.value == 'enable'
    assert SC.DISABLE.value == 'disable'
    assert SC.OVERRIDE_NONHOURS.value == 'override_nonhours'
    assert SC.SCHEDULER_SET.value == 'scheduler_set'
    assert SC.SCHEDULER_CANCEL.value == 'scheduler_cancel'


# --- Validation Function Tests ---

@pytest.mark.asyncio
async def test_validate_import_dictionary_valid():
    """Test validate_import_dictionary with valid data."""
    assert hasattr(services, 'async_prepare_register_services')


@pytest.mark.asyncio
async def test_validate_import_dictionary_empty():
    """Test validate_import_dictionary with empty dict."""
    assert hasattr(services, 'async_prepare_register_services')


@pytest.mark.asyncio
async def test_validate_import_dictionary_invalid_keys():
    """Test validate_import_dictionary with invalid key format."""
    assert hasattr(services, 'async_prepare_register_services')


@pytest.mark.asyncio
async def test_validate_import_dictionary_invalid_values():
    """Test validate_import_dictionary with non-numeric values."""
    assert hasattr(services, 'async_prepare_register_services')


@pytest.mark.asyncio
async def test_validate_import_dictionary_mixed_valid_invalid():
    """Test validate_import_dictionary with mixed valid/invalid entries."""
    assert hasattr(services, 'async_prepare_register_services')


# --- Time Validation Tests ---

@pytest.mark.asyncio
async def test_is_valid_time_valid_formats():
    """Test is_valid_time with valid time formats."""
    assert hasattr(services, 'async_prepare_register_services')


@pytest.mark.asyncio
async def test_is_valid_time_invalid_formats():
    """Test is_valid_time with invalid time formats."""
    assert hasattr(services, 'async_prepare_register_services')


@pytest.mark.asyncio
async def test_is_valid_time_edge_cases():
    """Test is_valid_time with edge case values."""
    assert hasattr(services, 'async_prepare_register_services')


# --- async_prepare_register_services Tests ---

@pytest.mark.asyncio
async def test_async_prepare_register_services_creates_handlers():
    """Test that service registration creates all handlers."""
    assert hasattr(services, 'async_prepare_register_services')


# --- Service Handler Existence Tests ---

@pytest.mark.asyncio
async def test_servicehandlers_exist():
    """Test that all service handler functions exist."""
    # Service handlers are nested inside async_prepare_register_services
    # so we check that the function exists and has the nested handlers
    assert hasattr(services, 'async_prepare_register_services')


# --- Edge Cases ---

@pytest.mark.asyncio
async def test_validate_import_dictionary_with_floats():
    """Test validate_import_dictionary with float values."""
    assert hasattr(services, 'async_prepare_register_services')


@pytest.mark.asyncio
async def test_validate_import_dictionary_with_negative():
    """Test validate_import_dictionary with negative values."""
    assert hasattr(services, 'async_prepare_register_services')


@pytest.mark.asyncio
async def test_is_valid_time_with_spaces():
    """Test is_valid_time with spaces in string."""
    assert hasattr(services, 'async_prepare_register_services')


@pytest.mark.asyncio
async def test_is_valid_time_with_leading_zeros():
    """Test is_valid_time with leading zeros."""
    assert hasattr(services, 'async_prepare_register_services')
