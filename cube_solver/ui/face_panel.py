"""Painel individual de cada face do cubo mágico (foto, câmera, grade 3x3 e orientação)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cube_solver.models.cube_state import COLOR_INFO, FACE_NAMES_PT, VALID_COLORS
from cube_solver.ui.camera_dialog import CameraCaptureDialog, bgr_to_qpixmap
from cube_solver.vision.detector import FaceDetectionResult, StickerDetector

# Guia de orientação relativa para exibir em cada painel
FACE_ORIENTATION_GUIDE: Dict[str, str] = {
    "U": "Topo: Trás (B) • Base: Frente (F) • Esq: Esquerda (L) • Dir: Direita (R)",
    "D": "Topo: Frente (F) • Base: Trás (B) • Esq: Esquerda (L) • Dir: Direita (R)",
    "F": "Topo: Cima (U) • Base: Baixo (D) • Esq: Esquerda (L) • Dir: Direita (R)",
    "B": "Topo: Cima (U) • Base: Baixo (D) • Esq: Direita (R) • Dir: Esquerda (L)",
    "L": "Topo: Cima (U) • Base: Baixo (D) • Esq: Trás (B) • Dir: Frente (F)",
    "R": "Topo: Cima (U) • Base: Baixo (D) • Esq: Frente (F) • Dir: Trás (B)",
}


class FacePanel(QGroupBox):
    """
    Painel de uma face do cubo (U, R, F, D, L, B) contendo:
      - Miniatura da foto carregada ou capturada pela câmera;
      - Grade 3x3 interativa de adesivos para edição/correção manual;
      - Botões de rotação de 90° (horário/anti-horário) para ajustar a orientação;
      - Caixa de confirmação de centro e orientação da face.
    """

    grid_changed = Signal(str)  # emite a letra da face ('U', 'R', 'F', 'D', 'L', 'B')
    confirmation_changed = Signal()

    def __init__(
        self,
        face_key: str,
        initial_grid: List[List[str]],
        get_active_brush: Callable[[], Optional[str]],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(FACE_NAMES_PT[face_key], parent)
        self.face_key = face_key
        self._grid: List[List[str]] = [row[:] for row in initial_grid]
        self._get_active_brush = get_active_brush
        self._annotated_bgr: Optional[np.ndarray] = None

        self._build_ui()
        self.refresh_grid_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 12, 8, 8)

        # Subtítulo de orientação da face
        guide_lbl = QLabel(FACE_ORIENTATION_GUIDE.get(self.face_key, ""))
        guide_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 400;")
        guide_lbl.setWordWrap(True)
        layout.addWidget(guide_lbl)

        # Linha principal: miniatura da foto + grade 3x3 de adesivos
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(8)

        # Miniatura da foto da face
        self.photo_label = QLabel("Sem foto\n(Manual)")
        self.photo_label.setFixedSize(96, 96)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: #0f172a; border: 1px dashed #334155; "
            "border-radius: 6px; color: #64748b; font-size: 11px;"
        )
        mid_layout.addWidget(self.photo_label)

        # Grade 3x3 de botões de adesivos
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(4)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        self.buttons: List[List[QPushButton]] = []
        for r in range(3):
            row_btns: List[QPushButton] = []
            for c in range(3):
                btn = QPushButton()
                btn.setFixedSize(36, 36)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(
                    lambda checked=False, rr=r, cc=c: self._on_sticker_clicked(rr, cc)
                )
                grid_layout.addWidget(btn, r, c)
                row_btns.append(btn)
            self.buttons.append(row_btns)

        mid_layout.addWidget(grid_widget)
        layout.addLayout(mid_layout)

        # Botões de ação da face: Foto, Câmera, Girar ↺ e Girar ↻
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        btn_photo = QPushButton("📁 Foto")
        btn_photo.setToolTip("Importar fotografia para esta face")
        btn_photo.clicked.connect(self.load_photo_dialog)
        btn_row.addWidget(btn_photo)

        btn_cam = QPushButton("📷 Câmera")
        btn_cam.setObjectName("cameraButton")
        btn_cam.setToolTip("Capturar esta face usando a webcam")
        btn_cam.clicked.connect(self.open_camera_for_face)
        btn_row.addWidget(btn_cam)

        btn_ccw = QPushButton("↺ 90°")
        btn_ccw.setToolTip("Girar orientação desta face 90° no sentido anti-horário")
        btn_ccw.clicked.connect(lambda: self.rotate_orientation(clockwise=False))
        btn_row.addWidget(btn_ccw)

        btn_cw = QPushButton("↻ 90°")
        btn_cw.setToolTip("Girar orientação desta face 90° no sentido horário")
        btn_cw.clicked.connect(lambda: self.rotate_orientation(clockwise=True))
        btn_row.addWidget(btn_cw)

        layout.addLayout(btn_row)

        # Checkbox de confirmação do centro e da orientação (Requisito 5)
        self.confirm_checkbox = QCheckBox("Centro e orientação confirmados")
        self.confirm_checkbox.setChecked(True)
        self.confirm_checkbox.stateChanged.connect(
            lambda _: self.confirmation_changed.emit()
        )
        layout.addWidget(self.confirm_checkbox)

    def _on_sticker_clicked(self, row: int, col: int) -> None:
        """Altera a cor do adesivo clicado usando o pincel ativo ou alternando em ciclo."""
        brush = self._get_active_brush()
        current = self._grid[row][col]
        if brush is not None and brush in VALID_COLORS:
            new_color = brush
        else:
            idx = VALID_COLORS.index(current) if current in VALID_COLORS else 0
            new_color = VALID_COLORS[(idx + 1) % len(VALID_COLORS)]

        self._grid[row][col] = new_color
        self.refresh_grid_ui()
        self.grid_changed.emit(self.face_key)

    def get_grid(self) -> List[List[str]]:
        """Retorna cópia da matriz 3x3 atual."""
        return [row[:] for row in self._grid]

    def set_grid(
        self,
        grid: List[List[str]],
        annotated_bgr: Optional[np.ndarray] = None,
        require_confirmation: bool = False,
    ) -> None:
        """Atualiza a grade 3x3 e opcionalmente a miniatura da foto."""
        self._grid = [row[:] for row in grid]
        if annotated_bgr is not None:
            self._annotated_bgr = annotated_bgr.copy()
            self._update_photo_preview()
        if require_confirmation:
            self.confirm_checkbox.setChecked(False)
        self.refresh_grid_ui()

    def clear_photo_preview(self) -> None:
        """Limpa a miniatura da foto carregada."""
        self._annotated_bgr = None
        self.photo_label.clear()
        self.photo_label.setText("Sem foto\n(Manual)")

    def _update_photo_preview(self) -> None:
        if self._annotated_bgr is None:
            self.clear_photo_preview()
            return
        pix = bgr_to_qpixmap(self._annotated_bgr, 92, 92)
        self.photo_label.setPixmap(pix)

    def refresh_grid_ui(self) -> None:
        """Atualiza as cores e rótulos dos 9 botões da grade 3x3."""
        for r in range(3):
            for c in range(3):
                col_code = self._grid[r][c]
                info = COLOR_INFO.get(col_code, COLOR_INFO["W"])
                is_center = r == 1 and c == 1
                border = (
                    "3px solid #0f172a; outline: 2px solid #38bdf8"
                    if is_center
                    else "1px solid #0f172a"
                )
                label_text = f"★{col_code}" if is_center else col_code
                self.buttons[r][c].setText(label_text)
                self.buttons[r][c].setToolTip(
                    f"{FACE_NAMES_PT[self.face_key]} [{r + 1},{c + 1}]: "
                    f"{info['name']} ({col_code})"
                    + (" — Centro da Face" if is_center else "")
                )
                self.buttons[r][c].setStyleSheet(
                    f"background-color: {info['hex']}; "
                    f"color: {info['text_color']}; "
                    f"border: {border}; "
                    "border-radius: 6px; "
                    "font-weight: 700; "
                    "font-size: 11px;"
                )

    def rotate_orientation(self, clockwise: bool = True) -> None:
        """Gira a grade 3x3 e a miniatura da imagem em 90 graus."""
        if clockwise:
            self._grid = [
                [self._grid[2 - r][c] for r in range(3)] for c in range(3)
            ]
            if self._annotated_bgr is not None:
                self._annotated_bgr = cv2.rotate(
                    self._annotated_bgr, cv2.ROTATE_90_CLOCKWISE
                )
        else:
            self._grid = [
                [self._grid[r][2 - c] for r in range(3)] for c in range(3)
            ]
            if self._annotated_bgr is not None:
                self._annotated_bgr = cv2.rotate(
                    self._annotated_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE
                )

        if self._annotated_bgr is not None:
            self._update_photo_preview()
        self.refresh_grid_ui()
        self.grid_changed.emit(self.face_key)

    def apply_detection_result(self, result: FaceDetectionResult) -> None:
        """Aplica o resultado do detector OpenCV neste painel."""
        if not result.success:
            QMessageBox.warning(
                self,
                f"Erro na Leitura — {FACE_NAMES_PT[self.face_key]}",
                result.error_message,
            )
            return
        self.set_grid(
            result.grid,
            annotated_bgr=result.annotated_image,
            require_confirmation=False,
        )
        self.grid_changed.emit(self.face_key)

    def load_photo_dialog(self) -> None:
        """Abre seletor de arquivo para importar uma imagem para esta face."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Selecionar fotografia para {FACE_NAMES_PT[self.face_key]}",
            str(Path.cwd()),
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not file_path:
            return
        result = StickerDetector.detect_face(file_path)
        self.apply_detection_result(result)

    def open_camera_for_face(self) -> None:
        """Abre o diálogo de captura via webcam para esta face específica."""
        dlg = CameraCaptureDialog(
            initial_face=self.face_key,
            single_face_mode=True,
            parent=self,
        )
        if dlg.exec() == CameraCaptureDialog.DialogCode.Accepted:
            if self.face_key in dlg.captured_results:
                self.apply_detection_result(dlg.captured_results[self.face_key])

    def is_confirmed(self) -> bool:
        """Indica se o centro e a orientação desta face estão confirmados."""
        return self.confirm_checkbox.isChecked()

    def set_confirmed(self, confirmed: bool) -> None:
        """Define o estado de confirmação da face."""
        self.confirm_checkbox.setChecked(confirmed)

