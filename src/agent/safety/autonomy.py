"""
Autonomy Level System

Defines autonomy levels (L1-L4) with threshold mappings for auto-execution
and provides a service to manage the current level per project.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Optional

from src.agent.safety.classification import RiskLevel


# Autonomy level type using Literal (per 07-01 decision pattern)
AutonomyLevel = Literal["L1", "L2", "L3", "L4"]


# Threshold mappings: which risk levels auto-execute at each autonomy level
AUTONOMY_THRESHOLDS: dict[AutonomyLevel, set[RiskLevel]] = {
    "L1": set(),                              # Nothing auto-executes (suggest only)
    "L2": {"safe"},                           # Only safe auto-executes
    "L3": {"safe", "moderate"},               # Safe + moderate auto-execute
    "L4": {"safe", "moderate", "destructive"},  # Only critical requires approval
}


# Human-readable labels for each level
AUTONOMY_LABELS: dict[AutonomyLevel, str] = {
    "L1": "Assistant",    # Most cautious - agent suggests only
    "L2": "Collaborator", # Default - safe actions auto-execute
    "L3": "Trusted",      # More autonomy for trusted projects
    "L4": "Expert",       # High autonomy - only critical needs approval
}


# Colors that harmonize with existing RISK_COLORS
AUTONOMY_COLORS: dict[AutonomyLevel, str] = {
    "L1": "#3B82F6",  # Blue - most cautious
    "L2": "#10B981",  # Emerald - collaborative (default)
    "L3": "#F59E0B",  # Amber - trusted
    "L4": "#EF4444",  # Red - expert/high autonomy
}
