"""Azure Functions app entry point."""

from __future__ import annotations

import base64
import binascii
import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import azure.functions as func

from prediction import (
    APPROVED_SHEET,
    generate_predictions,
    predictions_csv_to_excel_base64,
)

logger = logging.getLogger(__name__)

app = func.FunctionApp()


def _json_response(payload: dict[str, Any], status_code: int) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload),
        status_code=status_code,
        mimetype="application/json",
    )


@app.function_name(name="PredictFromWorkbook")
@app.route(route="predict", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def predict_from_workbook(req: func.HttpRequest) -> func.HttpResponse:
    """Generate predictions from a base64 encoded Excel workbook."""
    try:
        payload = req.get_json()
    except ValueError:
        logger.warning("Request body is not valid JSON")
        return _json_response({"error": "Invalid JSON body."}, status_code=400)

    workbook_b64 = payload.get("workbook_base64")
    if not workbook_b64:
        logger.warning("Missing workbook_base64 in request body")
        return _json_response(
            {"error": "Field 'workbook_base64' is required."},
            status_code=400,
        )

    approved_sheet = payload.get("approved_sheet") or APPROVED_SHEET

    try:
        workbook_bytes = base64.b64decode(workbook_b64)
    except (binascii.Error, ValueError):
        logger.warning("Failed to decode workbook_base64 input")
        return _json_response(
            {"error": "Field 'workbook_base64' must be valid base64."},
            status_code=400,
        )

    project_root = Path(__file__).resolve().parent
    models_root = project_root / "models"

    with TemporaryDirectory() as temp_dir:
        excel_path = Path(temp_dir) / "input.xlsx"
        output_path = Path(temp_dir) / "predictions.csv"
        excel_path.write_bytes(workbook_bytes)

        try:
            generate_predictions(
                excel_path=excel_path,
                models_root=models_root,
                output_path=output_path,
                approved_sheet=approved_sheet,
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("Prediction pipeline failed")
            return _json_response(
                {"error": "Prediction pipeline failed.", "details": str(exc)},
                status_code=500,
            )

        try:
            excel_base64 = predictions_csv_to_excel_base64(output_path)
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to prepare response workbook")
            return _json_response(
                {
                    "error": "Failed to prepare response workbook.",
                    "details": str(exc),
                },
                status_code=500,
            )

    response_payload = {"predictions_base64": excel_base64}

    return _json_response(response_payload, status_code=200)
