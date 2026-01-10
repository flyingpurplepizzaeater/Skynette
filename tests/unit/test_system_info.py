"""Unit tests for system information detection."""

def test_detect_available_ram():
    """Test RAM detection returns value in GB."""
    from src.ai.system_info import get_available_ram_gb

    ram_gb = get_available_ram_gb()

    assert ram_gb > 0
    assert isinstance(ram_gb, (int, float))


def test_has_cuda():
    """Test CUDA detection returns boolean."""
    from src.ai.system_info import has_cuda

    result = has_cuda()
    assert isinstance(result, bool)


def test_get_system_info():
    """Test get_system_info returns complete information."""
    from src.ai.system_info import get_system_info

    info = get_system_info()

    assert "ram_gb" in info
    assert "has_cuda" in info
    assert "platform" in info
    assert "architecture" in info


def test_can_run_model():
    """Test model compatibility check."""
    from src.ai.system_info import can_run_model

    # Test small model (should always work)
    assert can_run_model(0.1) is True

    # Test huge model (unlikely to work on most systems)
    # But don't fail test if system has massive RAM
    result = can_run_model(1000.0)
    assert isinstance(result, bool)
