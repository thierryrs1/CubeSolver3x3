"""Detecção automática dos 9 adesivos de uma face (ou planificação 6 faces) via OpenCV."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from cube_solver.vision.color_classifier import ColorClassifier


@dataclass
class FaceDetectionResult:
    """Resultado do processamento de imagem de uma face do cubo."""

    success: bool
    grid: List[List[str]] = field(default_factory=list)
    annotated_image: Optional[np.ndarray] = None
    original_image: Optional[np.ndarray] = None
    bgr_values: List[List[Tuple[int, int, int]]] = field(default_factory=list)
    error_message: str = ""


class StickerDetector:
    """
    Detector baseado em OpenCV para localizar os 9 adesivos de uma face 3x3
    a partir de uma fotografia ou extrair automaticamente as 6 faces de uma
    planificação (net) do cubo.
    """

    @staticmethod
    def load_image(path: str | Path) -> Optional[np.ndarray]:
        """
        Carrega uma imagem do disco suportando caminhos Windows com acentuação.
        """
        file_path = Path(path)
        if not file_path.exists() or not file_path.is_file():
            return None
        try:
            data = np.fromfile(str(file_path), dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
            return img
        except Exception:
            return None

    @staticmethod
    def _find_cube_roi(image: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Localiza a região de interesse (ROI: x, y, w, h) contendo a face 3x3 do cubo.
        Combina detecção de contornos quadrados/linhas escuras e saturação.
        Caso a imagem já esteja recortada na face, utiliza a imagem inteira com margem.
        """
        h_img, w_img = image.shape[:2]

        # 1. Tentar localizar contornos quadrados dos adesivos ou da borda do cubo
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 40, 130)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(
            dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )

        img_area = float(h_img * w_img)
        sticker_boxes: List[Tuple[int, int, int, int]] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Um adesivo individual costuma ocupar entre 1.5% e 15% da área da foto
            if area < img_area * 0.012 or area > img_area * 0.85:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                x, y, w, h = cv2.boundingRect(approx)
                aspect = w / float(h) if h > 0 else 0.0
                if 0.72 <= aspect <= 1.38 and area < img_area * 0.16:
                    sticker_boxes.append((x, y, w, h))

        # Se encontramos pelo menos 7 quadrados de adesivos cobrindo a grade 3x3, usamos seu envelope
        if len(sticker_boxes) >= 7:
            xs = [b[0] for b in sticker_boxes]
            ys = [b[1] for b in sticker_boxes]
            x2s = [b[0] + b[2] for b in sticker_boxes]
            y2s = [b[1] + b[3] for b in sticker_boxes]
            min_x, min_y = min(xs), min(ys)
            max_x, max_y = max(x2s), max(y2s)
            bw, bh = max_x - min_x, max_y - min_y
            if bw > w_img * 0.65 and bh > h_img * 0.65 and 0.75 <= (bw / bh) <= 1.35:
                return min_x, min_y, bw, bh

        # Fallback: se a imagem já é aproximadamente quadrada (foto recortada da face), usa toda a área
        aspect_img = w_img / float(h_img)
        if 0.78 <= aspect_img <= 1.28:
            return 0, 0, w_img, h_img

        side = int(min(w_img, h_img) * 0.88)
        x0 = (w_img - side) // 2
        y0 = (h_img - side) // 2
        return x0, y0, side, side

    @classmethod
    def detect_face_from_array(
        cls, image: np.ndarray, use_full_image: bool = False
    ) -> FaceDetectionResult:
        """
        Detecta e classifica os 9 adesivos de uma face 3x3 a partir de uma matriz BGR.
        """
        if image is None or image.size == 0:
            return FaceDetectionResult(
                success=False,
                error_message="Imagem vazia ou inválida.",
            )

        h_img, w_img = image.shape[:2]
        if h_img < 30 or w_img < 30:
            return FaceDetectionResult(
                success=False,
                error_message="A resolução da imagem é muito pequena para detectar os 9 adesivos.",
            )

        if use_full_image:
            rx, ry, rw, rh = 0, 0, w_img, h_img
        else:
            rx, ry, rw, rh = cls._find_cube_roi(image)
        cell_w = rw / 3.0
        cell_h = rh / 3.0

        patches: List[List[np.ndarray]] = []
        sample_boxes: List[List[Tuple[int, int, int, int]]] = []

        for r in range(3):
            row_patches: List[np.ndarray] = []
            row_boxes: List[Tuple[int, int, int, int]] = []
            for c in range(3):
                cx0 = int(rx + c * cell_w)
                cy0 = int(ry + r * cell_h)
                cx1 = int(rx + (c + 1) * cell_w)
                cy1 = int(ry + (r + 1) * cell_h)

                # Amostrar os 50% centrais da célula para evitar as bordas do adesivo
                pad_x = max(2, int((cx1 - cx0) * 0.24))
                pad_y = max(2, int((cy1 - cy0) * 0.24))
                sx0 = min(max(0, cx0 + pad_x), w_img - 1)
                sy0 = min(max(0, cy0 + pad_y), h_img - 1)
                sx1 = min(max(sx0 + 1, cx1 - pad_x), w_img)
                sy1 = min(max(sy0 + 1, cy1 - pad_y), h_img)

                patch = image[sy0:sy1, sx0:sx1]
                row_patches.append(patch)
                row_boxes.append((sx0, sy0, sx1, sy1))
            patches.append(row_patches)
            sample_boxes.append(row_boxes)

        grid_colors, bgr_grid = ColorClassifier.classify_grid_from_patches(patches)

        # Desenhar anotações visuais na imagem de preview
        annotated = image.copy()
        cv2.rectangle(
            annotated,
            (rx, ry),
            (rx + rw, ry + rh),
            (255, 255, 255),
            2,
        )
        for r in range(3):
            for c in range(3):
                sx0, sy0, sx1, sy1 = sample_boxes[r][c]
                col_code = grid_colors[r][c]
                disp_bgr = ColorClassifier.DISPLAY_BGR.get(col_code, (200, 200, 200))
                cv2.rectangle(annotated, (sx0, sy0), (sx1, sy1), (15, 23, 42), 3)
                cv2.rectangle(annotated, (sx0, sy0), (sx1, sy1), disp_bgr, 2)
                cv2.putText(
                    annotated,
                    col_code,
                    (sx0 + 4, sy1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    3,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    annotated,
                    col_code,
                    (sx0 + 4, sy1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

        return FaceDetectionResult(
            success=True,
            grid=grid_colors,
            annotated_image=annotated,
            original_image=image.copy(),
            bgr_values=bgr_grid,
        )

    @classmethod
    def detect_from_camera_frame(cls, frame: np.ndarray) -> FaceDetectionResult:
        """
        Processa um frame ao vivo da webcam usando uma mira quadrada 3x3 centralizada,
        desenhando o guia de alinhamento e classificando os 9 adesivos em tempo real.
        """
        if frame is None or frame.size == 0:
            return FaceDetectionResult(
                success=False,
                error_message="Frame da câmera inválido ou vazio.",
            )

        h_img, w_img = frame.shape[:2]
        side = int(min(w_img, h_img) * 0.62)
        rx = (w_img - side) // 2
        ry = (h_img - side) // 2
        cell_w = side / 3.0
        cell_h = side / 3.0

        patches: List[List[np.ndarray]] = []
        sample_boxes: List[List[Tuple[int, int, int, int]]] = []

        for r in range(3):
            row_patches: List[np.ndarray] = []
            row_boxes: List[Tuple[int, int, int, int]] = []
            for c in range(3):
                cx0 = int(rx + c * cell_w)
                cy0 = int(ry + r * cell_h)
                cx1 = int(rx + (c + 1) * cell_w)
                cy1 = int(ry + (r + 1) * cell_h)

                pad_x = max(4, int((cx1 - cx0) * 0.28))
                pad_y = max(4, int((cy1 - cy0) * 0.28))
                sx0 = cx0 + pad_x
                sy0 = cy0 + pad_y
                sx1 = cx1 - pad_x
                sy1 = cy1 - pad_y

                row_patches.append(frame[sy0:sy1, sx0:sx1])
                row_boxes.append((sx0, sy0, sx1, sy1))
            patches.append(row_patches)
            sample_boxes.append(row_boxes)

        grid_colors, bgr_grid = ColorClassifier.classify_grid_from_patches(patches)

        annotated = frame.copy()
        # Escurecer levemente a área externa à mira 3x3 para facilitar o alinhamento
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (w_img, h_img), (10, 15, 28), -1)
        annotated = cv2.addWeighted(overlay, 0.35, annotated, 0.65, 0)
        y_end = ry + side
        x_end = rx + side
        annotated[ry:y_end, rx:x_end] = frame[ry:y_end, rx:x_end]

        # Desenhar grade 3x3 da mira
        cv2.rectangle(
            annotated, (rx, ry), (rx + side, ry + side), (56, 189, 248), 2
        )
        for i in range(1, 3):
            gx = int(rx + i * cell_w)
            gy = int(ry + i * cell_h)
            cv2.line(annotated, (gx, ry), (gx, ry + side), (56, 189, 248), 1)
            cv2.line(annotated, (rx, gy), (rx + side, gy), (56, 189, 248), 1)

        # Desenhar caixas de amostragem com a cor detectada em tempo real
        for r in range(3):
            for c in range(3):
                sx0, sy0, sx1, sy1 = sample_boxes[r][c]
                col_code = grid_colors[r][c]
                disp_bgr = ColorClassifier.DISPLAY_BGR.get(col_code, (255, 255, 255))
                cv2.rectangle(annotated, (sx0, sy0), (sx1, sy1), (0, 0, 0), 3)
                cv2.rectangle(annotated, (sx0, sy0), (sx1, sy1), disp_bgr, 2)
                cv2.putText(
                    annotated,
                    col_code,
                    (sx0 + 5, sy1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 0, 0),
                    3,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    annotated,
                    col_code,
                    (sx0 + 5, sy1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

        crop_roi = frame[ry:y_end, rx:x_end].copy()
        return FaceDetectionResult(
            success=True,
            grid=grid_colors,
            annotated_image=annotated,
            original_image=crop_roi,
            bgr_values=bgr_grid,
        )

    @classmethod
    def detect_face(cls, image_path: str | Path) -> FaceDetectionResult:
        """
        Carrega uma fotografia de uma face a partir do caminho de arquivo e
        detecta seus 9 adesivos.
        """
        image = cls.load_image(image_path)
        if image is None:
            return FaceDetectionResult(
                success=False,
                error_message=f"Não foi possível abrir o arquivo de imagem: {image_path}",
            )
        return cls.detect_face_from_array(image)

    @classmethod
    def extract_net_faces(
        cls, image_path: str | Path
    ) -> Optional[Dict[str, FaceDetectionResult]]:
        """
        Extrai e classifica as 6 faces (U, L, F, R, B, D) de uma imagem de
        planificação em cruz (4 blocos de largura por 3 de altura, como cubo.png).
        """
        image = cls.load_image(image_path)
        if image is None:
            return None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Localiza as linhas de grade pretas da planificação
        black_mask = gray < 50
        ys, xs = np.where(black_mask)
        if len(xs) < 100 or len(ys) < 100:
            return None

        x0, y0 = int(xs.min()), int(ys.min())
        x1, y1 = int(xs.max()), int(ys.max())
        total_w = x1 - x0
        total_h = y1 - y0
        if total_w < 120 or total_h < 90:
            return None

        face_w = total_w / 4.0
        face_h = total_h / 3.0

        # Posições das 6 faces na cruz padrão:
        #       [U]
        # [L] [F] [R] [B]
        #       [D]
        layout: Dict[str, Tuple[int, int]] = {
            "U": (1, 0),
            "L": (0, 1),
            "F": (1, 1),
            "R": (2, 1),
            "B": (3, 1),
            "D": (1, 2),
        }

        results: Dict[str, FaceDetectionResult] = {}
        for face, (gx, gy) in layout.items():
            fx0 = int(round(x0 + gx * face_w))
            fy0 = int(round(y0 + gy * face_h))
            fx1 = int(round(x0 + (gx + 1) * face_w))
            fy1 = int(round(y0 + (gy + 1) * face_h))
            crop = image[fy0:fy1, fx0:fx1].copy()
            results[face] = cls.detect_face_from_array(crop, use_full_image=True)

        return results
