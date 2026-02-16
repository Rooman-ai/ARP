"""Data ingestion and feature engineering helpers."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Sequence

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

from .constants import COLUMN_ALIASES, FEATURE_COLUMNS

logger = logging.getLogger(__name__)


def read_specific_tables(file_path: Path, sheet_name: str) -> List[pd.DataFrame]:
    """Extracts property tables matching the expected Approved Revenue Forecast layout."""
    logger.debug("Reading sheet %s from %s", sheet_name, file_path)
    df_sheet = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    empty_rows = df_sheet[df_sheet.isnull().all(axis=1)].index.tolist()
    table_starts = [0] + [idx + 1 for idx in empty_rows]
    table_ends = empty_rows + [len(df_sheet)]

    required_keywords = {
        "Effected Beds",
        "Last Year",
        "Tier 1",
        "Property Totals",
        "Room/Rate Type",
    }

    property_pattern = re.compile(r".+\s-\s\d+x\d", re.IGNORECASE)

    extracted_tables: List[pd.DataFrame] = []

    for start, end in zip(table_starts, table_ends):
        candidate = df_sheet.iloc[start:end].dropna(how="all", axis=1)
        if candidate.empty:
            logger.debug("Skipping empty segment rows %s-%s", start, end)
            continue

        table_text = " ".join(candidate.fillna("").astype(str).head(5).values.flatten())
        if not all(keyword in table_text for keyword in required_keywords):
            logger.debug("Segment rows %s-%s missing keywords", start, end)
            continue

        candidate = candidate.reset_index(drop=True)
        first_row = candidate.iloc[0]
        if any(isinstance(cell, str) for cell in first_row):
            candidate.columns = first_row
            candidate = candidate.iloc[1:].reset_index(drop=True)

        def is_property_row(row: pd.Series) -> bool:
            return bool(property_pattern.match(" ".join(row.fillna("").astype(str))))

        filtered = candidate[candidate.apply(is_property_row, axis=1)].reset_index(
            drop=True
        )
        if filtered.empty:
            continue

        renamed_columns = list(filtered.columns)
        for idx, alias in enumerate(COLUMN_ALIASES):
            if idx < len(renamed_columns):
                renamed_columns[idx] = alias
        filtered.columns = renamed_columns

        filtered = filtered.iloc[:, : len(COLUMN_ALIASES)]
        extracted_tables.append(filtered)

    logger.info(
        "Extracted %s table(s) from sheet %s", len(extracted_tables), sheet_name
    )
    return extracted_tables


def load_sheet_dataframe(file_path: Path, sheet_name: str, prefix: str) -> pd.DataFrame:
    """Reads and concatenates all matching tables, then applies the requested prefix."""
    tables = read_specific_tables(file_path, sheet_name)
    if not tables:
        raise ValueError(
            f"No tables matching the expected format were found in sheet '{sheet_name}'."
        )

    combined = pd.concat(tables, ignore_index=True)
    combined = combined.add_prefix(f"{prefix}_")
    logger.info(
        "Combined dataframe for sheet %s has shape %s", sheet_name, combined.shape
    )
    return combined


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Adds engineered features required by the pre-trained models."""
    df = df.copy()
    with np.errstate(divide="ignore", invalid="ignore"):
        occupancy_ratio = df["approved_Effective Beds"].astype(float) / df[
            "approved_Property Totals"
        ].replace(0, np.nan)
        tier1_ratio = df["approved_Tier 1 Beds"].astype(float) / df[
            "approved_Effective Beds"
        ].replace(0, np.nan)

    df["approved_Occupancy_Ratio"] = occupancy_ratio.fillna(0.0)
    df["approved_Tier1_Ratio"] = tier1_ratio.fillna(0.0)
    df["approved_Price_Delta"] = df["approved_Tier 1 Base Rate"].astype(float) - df[
        "approved_Last Year Base Avg"
    ].astype(float)
    logger.info("Added engineered columns; dataframe now has shape %s", df.shape)
    return df


def ensure_numeric(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Coerces the specified columns to numeric, leaving originals untouched."""
    coerced = df.copy()
    for column in columns:
        coerced[column] = pd.to_numeric(coerced[column], errors="coerce")
    logger.debug("Coerced columns to numeric: %s", list(columns))
    return coerced


def prepare_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """Builds the model-ready feature matrix with median imputation."""
    numeric_df = ensure_numeric(df, FEATURE_COLUMNS)
    imputer = SimpleImputer(strategy="median")
    feature_matrix = imputer.fit_transform(numeric_df[FEATURE_COLUMNS])
    logger.info("Prepared feature matrix with shape %s", feature_matrix.shape)
    return feature_matrix
