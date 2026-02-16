#!/usr/bin/env python3
"""Convenience entrypoint for the prediction pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

from prediction import APPROVED_SHEET, DEFAULT_EXCEL, generate_predictions

logger = logging.getLogger(__name__)


def main() -> None:
    project_root = Path(__file__).resolve().parent
    excel_path = (project_root / DEFAULT_EXCEL).resolve()
    models_root = (project_root / "models").resolve()
    output_path = (project_root / "predicted_targets.csv").resolve()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )
    logger.info("Starting prediction generation pipeline")

    output_path = generate_predictions(
        excel_path=excel_path,
        models_root=models_root,
        output_path=output_path,
        approved_sheet=APPROVED_SHEET,
    )
    print(f"Wrote predictions to {output_path}")


if __name__ == "__main__":
    main()
