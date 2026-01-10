"""System information detection for AI model requirements."""

import platform
import psutil


def get_available_ram_gb() -> float:
    """Get available RAM in gigabytes."""
    try:
        mem = psutil.virtual_memory()
        return mem.total / (1024 ** 3)
    except Exception:
        return 0.0


def has_cuda() -> bool:
    """Check if CUDA GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def get_system_info() -> dict:
    """Get comprehensive system information."""
    return {
        "ram_gb": get_available_ram_gb(),
        "has_cuda": has_cuda(),
        "platform": platform.system(),
        "architecture": platform.machine(),
    }


def can_run_model(model_size_gb: float) -> bool:
    """Check if system can run a model of given size."""
    ram_gb = get_available_ram_gb()
    # Rule of thumb: need 1.5x model size in RAM
    required_ram = model_size_gb * 1.5
    return ram_gb >= required_ram
