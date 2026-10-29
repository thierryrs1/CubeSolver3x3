"""Módulo de visão computacional (OpenCV) para detecção e classificação dos adesivos."""

from .color_classifier import ColorClassifier
from .detector import FaceDetectionResult, StickerDetector

__all__ = ["ColorClassifier", "FaceDetectionResult", "StickerDetector"]
