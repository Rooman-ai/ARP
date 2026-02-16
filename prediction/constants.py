"""Shared constants for the prediction pipeline."""

from __future__ import annotations

APPROVED_SHEET = "Approved Rate Plan"
ADJUSTED_SHEET = "Adjusted Rate Plan"
DEFAULT_EXCEL = "Mark Athens Velocity Tracker 2026.xlsx"

FEATURE_COLUMNS = [
    "approved_Property Totals",
    "approved_Effective Beds",
    "approved_Last Year Base Avg",
    "approved_Last Year Eff Avg",
    "approved_Tier 1 Beds",
    "approved_Tier 1 Base Rate",
    "approved_Tier 1 Effective Rate",
    "approved_Occupancy_Ratio",
    "approved_Tier1_Ratio",
    "approved_Price_Delta",
]

TARGET_ORDER = [
    "adjusted_Effective Beds",
    "adjusted_Tier 1 Beds",
    "adjusted_Tier 1 Base Rate",
    "adjusted_Tier 1 Effective Rate",
]

COLUMN_ALIASES = [
    "Room/Rate Type",
    "Property Totals",
    "Effective Beds",
    "Last Year Base Avg",
    "Last Year Eff Avg",
    "Tier 1 Beds",
    "Tier 1 Base Rate",
    "Tier 1 Effective Rate",
]
