"""Model loading and inference utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, List

import cloudpickle  # type: ignore
import numpy as np

logger = logging.getLogger(__name__)

MODEL_TARGET_MAPPING: Dict[str, str] = {
    "tier-1-eff-beds": "adjusted_Effective Beds",
    "tier-1-beds": "adjusted_Tier 1 Beds",
    "tier-1-base-rate": "adjusted_Tier 1 Base Rate",
    "tier-1-eff-rate": "adjusted_Tier 1 Effective Rate",
}


def load_pickled_model(model_path: Path):
    """Loads a pickle/cloudpickle model file."""
    try:
        with model_path.open("rb") as handle:
            model = cloudpickle.load(handle)
        logger.info("Loaded model artifact from %s", model_path)
        return model
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to load model from {model_path}.") from exc


def discover_model_paths(root: Path) -> List[Path]:
    """Finds all model.pkl files under the provided root directory."""
    model_paths: List[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        candidate = child / "model" / "model.pkl"
        if candidate.exists():
            model_paths.append(candidate)
            logger.debug("Discovered model file at %s", candidate)
    logger.info("Found %s model.pkl file(s) under %s", len(model_paths), root)
    return model_paths


def predict_targets(
    feature_matrix: np.ndarray,
    model_paths: Iterable[Path],
) -> Dict[str, np.ndarray]:
    """Runs inference with each model and returns a dictionary keyed by target name."""
    raw_predictions: Dict[str, np.ndarray] = {}

    for path in model_paths:
        model = load_pickled_model(path)
        preds = model.predict(feature_matrix)
        key = path.parent.parent.name
        raw_predictions[key] = preds
        logger.info(
            "Generated predictions with shape %s from model %s", preds.shape, key
        )

    final_predictions: Dict[str, np.ndarray] = {}
    for model_key, preds in raw_predictions.items():
        target = MODEL_TARGET_MAPPING.get(model_key)
        if target is None:
            raise RuntimeError(
                f"No target mapping found for model folder '{model_key}'."
            )
        if "Beds" in target:
            preds = np.round(preds)
        elif "Rate" in target:
            preds = np.round(preds.astype(float), 1)
        final_predictions[target] = preds
        logger.info("Assigned predictions from %s to target %s", model_key, target)

    return final_predictions
