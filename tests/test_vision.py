"""Testes automatizados para o módulo de visão computacional (OpenCV)."""

from pathlib import Path

import cv2
import numpy as np

from cube_solver.models.cube_state import CubeState
from cube_solver.solver.kociemba_solver import CubeSolverEngine
from cube_solver.vision.color_classifier import ColorClassifier
from cube_solver.vision.detector import StickerDetector


def _create_synthetic_face_image(grid: list[list[str]], size: int = 300) -> np.ndarray:
    """Cria uma imagem BGR sintética de uma face 3x3 para testes."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    cell = size // 3
    for r in range(3):
        for c in range(3):
            bgr = ColorClassifier.DISPLAY_BGR[grid[r][c]]
            x0, y0 = c * cell + 6, r * cell + 6
            x1, y1 = (c + 1) * cell - 6, (r + 1) * cell - 6
            cv2.rectangle(img, (x0, y0), (x1, y1), bgr, -1)
    return img


def test_detect_synthetic_face() -> None:
    """Deve detectar com precisão todas as 6 cores em uma face 3x3 sintética."""
    target_grid = [
        ["W", "R", "G"],
        ["Y", "O", "B"],
        ["B", "G", "W"],
    ]
    img = _create_synthetic_face_image(target_grid)
    res = StickerDetector.detect_face_from_array(img)
    assert res.success is True
    assert res.grid == target_grid
    assert res.annotated_image is not None


def test_detect_from_camera_frame() -> None:
    """Deve detectar os 9 adesivos posicionados na mira central de um frame de câmera."""
    target_grid = [
        ["R", "W", "B"],
        ["G", "Y", "O"],
        ["W", "R", "G"],
    ]
    frame = np.full((480, 640, 3), 40, dtype=np.uint8)
    side = int(min(640, 480) * 0.62)
    rx = (640 - side) // 2
    ry = (480 - side) // 2
    face_img = _create_synthetic_face_image(target_grid, size=side)
    y_end = ry + side
    x_end = rx + side
    frame[ry:y_end, rx:x_end] = face_img

    res = StickerDetector.detect_from_camera_frame(frame)
    assert res.success is True
    assert res.grid == target_grid
    assert res.annotated_image is not None


def test_extract_cubo_png_net() -> None:
    """Deve extrair todas as 6 faces de cubo.png e resolver o cubo automaticamente."""
    net_path = Path(__file__).resolve().parent.parent / "cubo.png"
    if not net_path.exists():
        return
    faces_result = StickerDetector.extract_net_faces(net_path)
    assert faces_result is not None
    assert len(faces_result) == 6

    faces_dict = {face: res.grid for face, res in faces_result.items()}
    cube = CubeState(faces_dict)
    solution = CubeSolverEngine.solve(cube)
    assert solution.success is True
    assert len(solution.moves) > 0


def test_detect_six_individual_face_photos() -> None:
    """Deve carregar as 6 fotos individuais de exemplos_faces/ e resolver o cubo."""
    examples_dir = Path(__file__).resolve().parent.parent / "exemplos_faces"
    if not examples_dir.exists():
        return
    mapping = {
        "U": "1_cima_U.png",
        "F": "2_frente_F.png",
        "R": "3_direita_R.png",
        "B": "4_tras_B.png",
        "L": "5_esquerda_L.png",
        "D": "6_baixo_D.png",
    }
    faces_dict = {}
    for face, filename in mapping.items():
        res = StickerDetector.detect_face(examples_dir / filename)
        assert res.success is True
        faces_dict[face] = res.grid

    cube = CubeState(faces_dict)
    solution = CubeSolverEngine.solve(cube)
    assert solution.success is True
    assert len(solution.moves) > 0
