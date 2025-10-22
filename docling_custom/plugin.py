from __future__ import annotations

from docling.models.custom_api_ocr_model import CustomApiOcrModel


def register():
    return {
        "ocr_engines": [
            CustomApiOcrModel,
        ]
    }
