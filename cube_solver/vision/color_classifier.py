"""Classificação de cores de adesivos do cubo mágico em espaço HSV e BGR."""

from __future__ import annotations

from typing import Dict, List, Tuple

import cv2
import numpy as np


class ColorClassifier:
    """
    Classifica uma amostra BGR/HSV de um adesivo em uma das 6 cores padrão:
    'W' (Branco), 'R' (Vermelho), 'O' (Laranja), 'Y' (Amarelo), 'G' (Verde), 'B' (Azul).
    """

    # Cores de referência em BGR para visualização de sobreposição (overlay)
    DISPLAY_BGR: Dict[str, Tuple[int, int, int]] = {
        "W": (245, 245, 245),
        "R": (50, 50, 235),
        "G": (80, 195, 35),
        "Y": (20, 225, 250),
        "O": (30, 130, 245),
        "B": (225, 95, 30),
    }

    @staticmethod
    def extract_dominant_bgr(patch: np.ndarray) -> Tuple[int, int, int]:
        """
        Extrai a cor BGR representativa de um recorte (patch) do adesivo,
        ignorando pixels escuros de borda ou letras impressas no centro.
        """
        if patch is None or patch.size == 0:
            return (255, 255, 255)

        pixels = patch.reshape(-1, 3)
        # Filtra pixels muito escuros (bordas pretas, sombras fortes ou letras como 'U', 'F')
        brightness = np.max(pixels, axis=1)
        valid_mask = brightness > 55
        if np.count_nonzero(valid_mask) >= max(5, len(pixels) // 10):
            filtered = pixels[valid_mask]
        else:
            filtered = pixels

        median_bgr = np.median(filtered, axis=0)
        return (int(median_bgr[0]), int(median_bgr[1]), int(median_bgr[2]))

    @classmethod
    def classify_bgr(cls, bgr: Tuple[int, int, int]) -> str:
        """
        Classifica uma tupla (B, G, R) em 'W', 'R', 'O', 'Y', 'G' ou 'B'
        utilizando espaço de cor HSV do OpenCV (H: 0..179, S: 0..255, V: 0..255).
        """
        pixel = np.uint8([[list(bgr)]])
        hsv = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])

        # Branco: baixa saturação e brilho moderado/alto
        if s < 50 and v > 125:
            return "W"

        # Caso de iluminação mais escura mas acromática
        if s < 32:
            return "W"

        # Vermelho fica nas extremidades do círculo de matiz (Hue)
        if h <= 7 or h >= 162:
            return "R"

        # Laranja (inclui tons laranja-avermelhados e laranja-dourados)
        if 8 <= h <= 24:
            return "O"

        # Amarelo
        if 25 <= h <= 38:
            return "Y"

        # Verde
        if 39 <= h <= 88:
            return "G"

        # Azul
        if 89 <= h <= 145:
            return "B"

        # Fallback entre Laranja/Vermelho para tons rosados/avermelhados (146..161)
        return "R"

    @classmethod
    def classify_grid_from_patches(
        cls, patches: List[List[np.ndarray]]
    ) -> Tuple[List[List[str]], List[List[Tuple[int, int, int]]]]:
        """
        Recebe uma matriz 3x3 de recortes (patches) de uma face e retorna
        a matriz 3x3 de cores classificadas e a matriz 3x3 de valores BGR médios.
        """
        colors: List[List[str]] = []
        bgr_grid: List[List[Tuple[int, int, int]]] = []
        for r in range(3):
            row_colors: List[str] = []
            row_bgrs: List[Tuple[int, int, int]] = []
            for c in range(3):
                bgr = cls.extract_dominant_bgr(patches[r][c])
                color = cls.classify_bgr(bgr)
                row_bgrs.append(bgr)
                row_colors.append(color)
            colors.append(row_colors)
            bgr_grid.append(row_bgrs)
        return colors, bgr_grid
