"""High-level orchestration utilities for generating predictions."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from prediction.data_processing import (
    add_derived_columns,
    load_sheet_dataframe,
    prepare_feature_matrix,
)
from prediction.model_utils import discover_model_paths, predict_targets

logger = logging.getLogger(__name__)


def add_predictions_to_dataframe(
    approved_df: pd.DataFrame,
    predictions: Mapping[str, np.ndarray],
) -> pd.DataFrame:
    """Adds prediction columns to the approved dataframe."""
    result = approved_df.copy()
    for target, values in predictions.items():
        column_name = f"predicted_{target}"
        result[column_name] = values
        logger.debug("Added column %s to output dataframe", column_name)
    logger.info("Output dataframe shape after adding predictions: %s", result.shape)
    return result


def generate_predictions(
    excel_path: Path,
    models_root: Path,
    output_path: Path,
    approved_sheet: str,
) -> Path:
    """Executes the end-to-end prediction workflow."""
    logger.info("Running prediction pipeline for workbook %s", excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel workbook not found at {excel_path}.")

    approved_df = load_sheet_dataframe(excel_path, approved_sheet, "approved")
    approved_df = add_derived_columns(approved_df)

    feature_matrix = prepare_feature_matrix(approved_df)

    model_paths = discover_model_paths(models_root)
    if not model_paths:
        raise RuntimeError(f"No model.pkl files were found under {models_root}.")

    predictions = predict_targets(
        feature_matrix,
        model_paths,
    )

    output_df = add_predictions_to_dataframe(approved_df, predictions)
    output_df.to_csv(output_path, index=False)
    logger.info("Wrote predictions to %s", output_path)
    return output_path
