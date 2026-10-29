"""Diálogo interativo de captura por câmera (Webcam) com mira 3x3 em tempo real."""

from __future__ import annotations

from typing import Dict, List, Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QKeyEvent, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cube_solver.models.cube_state import COLOR_INFO, FACE_NAMES_PT, FACE_ORDER
from cube_solver.vision.detector import FaceDetectionResult, StickerDetector

# Dicas de orientação para ajudar o usuário a segurar o cubo diante da câmera
FACE_CAMERA_TIPS: Dict[str, str] = {
    "U": "Aponte a face de CIMA (U) para a câmera, mantendo a face de TRÁS (B) voltada para o topo.",
    "F": "Aponte a face da FRENTE (F) para a câmera, mantendo a face de CIMA (U) voltada para o topo.",
    "R": "Aponte a face da DIREITA (R) para a câmera, mantendo a face de CIMA (U) voltada para o topo.",
    "B": "Aponte a face de TRÁS (B) para a câmera, mantendo a face de CIMA (U) voltada para o topo.",
    "L": "Aponte a face da ESQUERDA (L) para a câmera, mantendo a face de CIMA (U) voltada para o topo.",
    "D": "Aponte a face de BAIXO (D) para a câmera, mantendo a face da FRENTE (F) voltada para o topo.",
}


def bgr_to_qpixmap(bgr_img: np.ndarray, max_w: int, max_h: int) -> QPixmap:
    """Converte uma matriz BGR do OpenCV em QPixmap redimensionado."""
    rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
    pixmap = QPixmap.fromImage(qimg)
    return pixmap.scaled(
        max_w,
        max_h,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


class CameraCaptureDialog(QDialog):
    """
    Assistente de captura por câmera (Webcam) usando OpenCV.
    Permite capturar uma única face ou todas as 6 faces em sequência guiada,
    mostrando uma mira 3x3 ao vivo e prévia instantânea das cores detectadas.
    """

    def __init__(
        self,
        initial_face: str = "F",
        single_face_mode: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.single_face_mode = single_face_mode
        self.current_face = initial_face if initial_face in FACE_ORDER else "F"
        self.captured_results: Dict[str, FaceDetectionResult] = {}
        self.latest_detection: Optional[FaceDetectionResult] = None
        self.cap: Optional[cv2.VideoCapture] = None

        self.setWindowTitle(
            f"Captura por Câmera — {FACE_NAMES_PT[self.current_face]}"
            if single_face_mode
            else "Assistente de Câmera — Capturar Faces do Cubo"
        )
        self.resize(860, 560)

        self._build_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self._start_camera(0)

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(10)

        # Barra superior: seleção de câmera, face alvo e espelhamento
        top_bar = QHBoxLayout()

        top_bar.addWidget(QLabel("Face Alvo:"))
        self.face_combo = QComboBox()
        for f in FACE_ORDER:
            self.face_combo.addItem(FACE_NAMES_PT[f], userData=f)
        idx = FACE_ORDER.index(self.current_face)
        self.face_combo.setCurrentIndex(idx)
        self.face_combo.currentIndexChanged.connect(self._on_face_changed)
        if self.single_face_mode:
            self.face_combo.setEnabled(False)
        top_bar.addWidget(self.face_combo)

        top_bar.addSpacing(12)
        top_bar.addWidget(QLabel("Dispositivo:"))
        self.cam_combo = QComboBox()
        self.cam_combo.addItem("Câmera 0 (Padrão)", userData=0)
        self.cam_combo.addItem("Câmera 1 (Secundária)", userData=1)
        self.cam_combo.addItem("Câmera 2", userData=2)
        self.cam_combo.currentIndexChanged.connect(self._on_camera_changed)
        top_bar.addWidget(self.cam_combo)

        self.mirror_check = QCheckBox("Espelhar vídeo horizontalmente")
        self.mirror_check.setChecked(False)
        top_bar.addWidget(self.mirror_check)
        top_bar.addStretch()

        root_layout.addLayout(top_bar)

        # Dica de posicionamento da face atual
        self.tip_label = QLabel()
        self.tip_label.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; padding: 8px 12px; "
            "border-radius: 6px; font-weight: 600; border: 1px solid #334155;"
        )
        self.tip_label.setWordWrap(True)
        root_layout.addWidget(self.tip_label)
        self._update_tip_text()

        # Área central: vídeo ao vivo à esquerda e prévia 3x3 detectada à direita
        center_layout = QHBoxLayout()

        self.video_label = QLabel("Inicializando câmera...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(520, 390)
        self.video_label.setStyleSheet(
            "background-color: #090d16; border: 2px solid #26354d; border-radius: 10px;"
        )
        center_layout.addWidget(self.video_label, stretch=3)

        # Painel lateral de prévia em tempo real
        side_box = QGroupBox("Prévia Ao Vivo (Grade 3x3)")
        side_layout = QVBoxLayout(side_box)

        self.preview_cells: List[List[QLabel]] = []
        grid_layout = QGridLayout()
        grid_layout.setSpacing(6)
        for r in range(3):
            row_labels: List[QLabel] = []
            for c in range(3):
                lbl = QLabel("?")
                lbl.setFixedSize(62, 62)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet(
                    "background-color: #334155; color: #ffffff; "
                    "border-radius: 8px; font-weight: 700; font-size: 15px;"
                )
                grid_layout.addWidget(lbl, r, c)
                row_labels.append(lbl)
            self.preview_cells.append(row_labels)

        side_layout.addLayout(grid_layout)
        side_layout.addSpacing(10)

        self.status_label = QLabel(
            "Posicione o cubo dentro da grade azul central e clique em Capturar (ou pressione Espaço)."
        )
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        side_layout.addWidget(self.status_label)

        self.captured_count_label = QLabel("Faces capturadas nesta sessão: 0/6")
        self.captured_count_label.setStyleSheet(
            "color: #34d399; font-weight: 700; font-size: 13px;"
        )
        if self.single_face_mode:
            self.captured_count_label.hide()
        side_layout.addWidget(self.captured_count_label)

        side_layout.addStretch()

        self.btn_capture = QPushButton("📸 Capturar Face Atual (Espaço)")
        self.btn_capture.setObjectName("primaryButton")
        self.btn_capture.clicked.connect(self.capture_current_face)
        side_layout.addWidget(self.btn_capture)

        self.btn_finish = QPushButton("✔ Concluir e Usar Capturas")
        self.btn_finish.setObjectName("successButton")
        self.btn_finish.clicked.connect(self.accept)
        side_layout.addWidget(self.btn_finish)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        side_layout.addWidget(btn_cancel)

        center_layout.addWidget(side_box, stretch=1)
        root_layout.addLayout(center_layout)

    def _update_tip_text(self) -> None:
        tip = FACE_CAMERA_TIPS.get(self.current_face, "")
        self.tip_label.setText(
            f"🎯 Capturando {FACE_NAMES_PT[self.current_face]}: {tip}"
        )

    def _on_face_changed(self, index: int) -> None:
        face = self.face_combo.itemData(index)
        if face:
            self.current_face = face
            self._update_tip_text()

    def _on_camera_changed(self, index: int) -> None:
        cam_id = self.cam_combo.itemData(index)
        if cam_id is not None:
            self._start_camera(int(cam_id))

    def _start_camera(self, cam_index: int) -> None:
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        # Tenta abrir com DirectShow no Windows para inicialização mais rápida
        cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(cam_index)

        if not cap.isOpened():
            self.video_label.setText(
                f"⚠ Nenhuma webcam encontrada no Dispositivo {cam_index}.\n\n"
                "Conecte uma câmera ou utilize os botões '📁 Foto' / '🧩 Importar Planificação'."
            )
            self.btn_capture.setEnabled(False)
            return

        self.cap = cap
        self.btn_capture.setEnabled(True)
        self.timer.start(35)

    def _update_frame(self) -> None:
        if self.cap is None or not self.cap.isOpened():
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return

        if self.mirror_check.isChecked():
            frame = cv2.flip(frame, 1)

        detection = StickerDetector.detect_from_camera_frame(frame)
        self.latest_detection = detection

        if detection.success and detection.annotated_image is not None:
            pix = bgr_to_qpixmap(
                detection.annotated_image,
                self.video_label.width() - 8,
                self.video_label.height() - 8,
            )
            self.video_label.setPixmap(pix)

            for r in range(3):
                for c in range(3):
                    col_code = detection.grid[r][c]
                    info = COLOR_INFO[col_code]
                    self.preview_cells[r][c].setText(col_code)
                    self.preview_cells[r][c].setStyleSheet(
                        f"background-color: {info['hex']}; color: {info['text_color']}; "
                        "border: 2px solid #0f172a; border-radius: 8px; "
                        "font-weight: 700; font-size: 15px;"
                    )

    def capture_current_face(self) -> None:
        """Salva a detecção atual para a face selecionada."""
        if self.latest_detection is None or not self.latest_detection.success:
            QMessageBox.warning(
                self,
                "Câmera indisponível",
                "Não há imagem válida da câmera para capturar no momento.",
            )
            return

        self.captured_results[self.current_face] = self.latest_detection
        self.captured_count_label.setText(
            f"Faces capturadas nesta sessão: {len(self.captured_results)}/6"
        )

        if self.single_face_mode:
            self.accept()
            return

        # Avança automaticamente para a próxima face ainda não capturada
        curr_idx = FACE_ORDER.index(self.current_face)
        for offset in range(1, 7):
            next_idx = (curr_idx + offset) % 6
            next_face = FACE_ORDER[next_idx]
            if next_face not in self.captured_results:
                self.face_combo.setCurrentIndex(next_idx)
                self.status_label.setText(
                    f"✔ {FACE_NAMES_PT[FACE_ORDER[curr_idx]]} capturada! "
                    f"Agora posicione {FACE_NAMES_PT[next_face]}."
                )
                return

        # Se todas as 6 foram capturadas, informa o usuário
        self.status_label.setText(
            "🎉 Todas as 6 faces foram capturadas! Clique em 'Concluir e Usar Capturas'."
        )

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and self.btn_capture.isEnabled():
            self.capture_current_face()
            return
        super().keyPressEvent(event)

    def _release_camera(self) -> None:
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def accept(self) -> None:
        self._release_camera()
        super().accept()

    def reject(self) -> None:
        self._release_camera()
        super().reject()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._release_camera()
        super().closeEvent(event)

