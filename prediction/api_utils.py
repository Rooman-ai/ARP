"""Helpers for adapting pipeline output for the HTTP API."""

from __future__ import annotations

import base64
import logging
from io import BytesIO
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def _strip_prefix(column: str) -> str:
    return column[9:] if column.startswith("approved_") else column


def predictions_csv_to_excel_base64(csv_path: Path) -> str:
    """Convert the CSV produced by the prediction pipeline into an Excel base64 payload."""
    try:
        dataframe = pd.read_csv(csv_path)
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Failed to load pipeline output.") from exc

    # Strip "approved_" prefix
    dataframe.columns = [_strip_prefix(column) for column in dataframe.columns]

    # Drop unwanted columns
    drop_columns = [
        "Tier 1 Beds",
        "Tier 1 Base Rate",
        "Tier 1 Effective Rate",
        "predicted_adjusted_Tier 1 Beds",
        "Effective Beds",
    ]
    dataframe = dataframe.drop(
        columns=[col for col in drop_columns if col in dataframe.columns]
    )

    # Rename predicted adjusted column
    if "predicted_adjusted_Effective Beds" in dataframe.columns:
        dataframe = dataframe.rename(
            columns={"predicted_adjusted_Effective Beds": "predicted_Effected Beds"}
        )

        # Move "predicted_Effected Beds" to third position
        if "predicted_Effected Beds" in dataframe.columns:
            cols = list(dataframe.columns)
            cols.insert(2, cols.pop(cols.index("predicted_Effected Beds")))
            dataframe = dataframe[cols]

    # Convert to Excel in memory
    buffer = BytesIO()
    dataframe.to_excel(buffer, index=False)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("ascii")
