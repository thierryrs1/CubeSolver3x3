"""Janela principal do aplicativo desktop CubeSolver."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from cube_solver.models.cube_state import (
    COLOR_INFO,
    FACE_NAMES_PT,
    FACE_ORDER,
    VALID_COLORS,
    CubeState,
)
from cube_solver.solver.kociemba_solver import CubeSolverEngine
from cube_solver.ui.camera_dialog import CameraCaptureDialog
from cube_solver.ui.face_panel import FacePanel
from cube_solver.ui.solution_panel import SolutionPanel
from cube_solver.ui.styles import DARK_STYLESHEET
from cube_solver.validation.validator import CubeValidator
from cube_solver.viewer3d.viewer_widget import Cube3DViewerWidget
from cube_solver.vision.detector import StickerDetector

# Ordem visual intuitiva para os 6 painéis na grade 2x3
PANEL_DISPLAY_ORDER: List[str] = ["U", "D", "F", "B", "L", "R"]


class MainWindow(QMainWindow):
    """
    Janela principal do CubeSolver integrando:
      - Painéis das 6 faces (Cima, Baixo, Frente, Trás, Esquerda, Direita);
      - Importação de 6 fotos individuais, planificação (cubo.png) ou captura por câmera (Webcam);
      - Paleta de cores para preenchimento e correção manual rápida;
      - Visualizador 3D interativo em Three.js;
      - Validador físico e motor determinístico Kociemba com reprodução passo a passo.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(
            "CubeSolver — Resolvedor de Cubo Mágico 3x3x3 (OpenCV + Kociemba + Three.js)"
        )
        self.resize(1380, 860)
        self.setStyleSheet(DARK_STYLESHEET)

        self.cube_state = CubeState.solved()
        self.active_brush: Optional[str] = None  # None = alternar em ciclo ao clicar
        self.face_panels: Dict[str, FacePanel] = {}
        self.brush_buttons: Dict[Optional[str], QPushButton] = {}

        self._build_ui()
        self._sync_state_from_panels()

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 10, 12, 10)
        root_layout.setSpacing(8)

        # 1. Cabeçalho e Barra de Ferramentas Principal
        header_bar = QHBoxLayout()
        header_bar.setSpacing(8)

        title_lbl = QLabel("🧊 CubeSolver 3x3x3")
        title_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: #38bdf8; padding-right: 8px;"
        )
        header_bar.addWidget(title_lbl)

        btn_camera_wizard = QPushButton("📷 Assistente de Câmera (Webcam)")
        btn_camera_wizard.setObjectName("cameraButton")
        btn_camera_wizard.setToolTip(
            "Abrir assistente com mira 3x3 ao vivo para capturar as faces pela câmera"
        )
        btn_camera_wizard.clicked.connect(self.open_camera_wizard)
        header_bar.addWidget(btn_camera_wizard)

        btn_load_six = QPushButton("📁 Importar 6 Fotos")
        btn_load_six.setToolTip(
            "Selecionar até 6 fotografias (uma para cada face do cubo)"
        )
        btn_load_six.clicked.connect(self.import_six_photos_dialog)
        header_bar.addWidget(btn_load_six)

        btn_load_net = QPushButton("🧩 Importar Planificação (cubo.png)")
        btn_load_net.setToolTip(
            "Extrair automaticamente as 6 faces de uma imagem de planificação em cruz"
        )
        btn_load_net.clicked.connect(self.import_net_image_dialog)
        header_bar.addWidget(btn_load_net)

        btn_scramble = QPushButton("🎲 Embaralhar Exemplo")
        btn_scramble.setToolTip("Gerar um embaralhamento válido para testar a solução")
        btn_scramble.clicked.connect(self.load_random_scramble)
        header_bar.addWidget(btn_scramble)

        btn_reset = QPushButton("🔄 Resetar Cubo")
        btn_reset.setToolTip("Restaurar todas as faces para o estado resolvido")
        btn_reset.clicked.connect(self.reset_to_solved)
        header_bar.addWidget(btn_reset)

        header_bar.addStretch()

        btn_solve = QPushButton("🚀 Validar e Resolver Cubo")
        btn_solve.setObjectName("primaryButton")
        btn_solve.clicked.connect(self.validate_and_solve)
        header_bar.addWidget(btn_solve)

        root_layout.addLayout(header_bar)

        # 2. Barra de Paleta de Cores (Correção Manual) + Confirmação Geral
        palette_bar = QHBoxLayout()
        palette_bar.setSpacing(6)

        palette_lbl = QLabel("🎨 Pincel de Correção Manual:")
        palette_lbl.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        palette_bar.addWidget(palette_lbl)

        btn_cycle = QPushButton("🔄 Alternar ao Clicar")
        btn_cycle.clicked.connect(lambda: self._set_active_brush(None))
        palette_bar.addWidget(btn_cycle)
        self.brush_buttons[None] = btn_cycle

        for col_code in VALID_COLORS:
            info = COLOR_INFO[col_code]
            btn_col = QPushButton(f"{info['name']} ({col_code})")
            btn_col.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_col.clicked.connect(
                lambda checked=False, cc=col_code: self._set_active_brush(cc)
            )
            palette_bar.addWidget(btn_col)
            self.brush_buttons[col_code] = btn_col

        palette_bar.addStretch()

        btn_confirm_all = QPushButton("✔ Confirmar Centros e Orientações (Todas)")
        btn_confirm_all.setObjectName("successButton")
        btn_confirm_all.clicked.connect(self.confirm_all_faces)
        palette_bar.addWidget(btn_confirm_all)

        root_layout.addLayout(palette_bar)
        self._refresh_brush_buttons()

        # 3. Área Principal Dividida: Esquerda (6 Painéis de Faces) | Direita (3D + Solução)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Coluna Esquerda: 6 Painéis das Faces em Grade 2x3 dentro de QScrollArea
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(620)

        faces_container = QWidget()
        faces_grid = QGridLayout(faces_container)
        faces_grid.setSpacing(10)
        faces_grid.setContentsMargins(4, 4, 4, 4)

        for idx, face_key in enumerate(PANEL_DISPLAY_ORDER):
            panel = FacePanel(
                face_key=face_key,
                initial_grid=self.cube_state.get_face(face_key),
                get_active_brush=lambda: self.active_brush,
                parent=faces_container,
            )
            panel.grid_changed.connect(self._on_panel_grid_changed)
            row = idx // 2
            col = idx % 2
            faces_grid.addWidget(panel, row, col)
            self.face_panels[face_key] = panel

        left_scroll.setWidget(faces_container)
        splitter.addWidget(left_scroll)

        # Coluna Direita: Visualizador 3D Three.js + Painel de Solução e Controle
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(8)

        viewer_group = QGroupBox("Visualização e Animação 3D Interativa (Three.js)")
        viewer_layout = QVBoxLayout(viewer_group)
        viewer_layout.setContentsMargins(6, 10, 6, 6)
        self.viewer_3d = Cube3DViewerWidget(viewer_group)
        viewer_layout.addWidget(self.viewer_3d)
        right_layout.addWidget(viewer_group, stretch=5)

        self.solution_panel = SolutionPanel(right_container)
        self.solution_panel.request_3d_sync.connect(self.viewer_3d.set_cube_state)
        self.solution_panel.request_3d_animate.connect(self.viewer_3d.animate_move)
        right_layout.addWidget(self.solution_panel, stretch=4)

        splitter.addWidget(right_container)
        splitter.setSizes([650, 710])

        root_layout.addWidget(splitter, stretch=1)

        self.statusBar().showMessage(
            "Pronto. Dica: Clique nos adesivos para corrigir cores manualmente, "
            "use '📷 Assistente de Câmera' ou importe fotos das 6 faces."
        )

    def _set_active_brush(self, color_code: Optional[str]) -> None:
        self.active_brush = color_code
        self._refresh_brush_buttons()

    def _refresh_brush_buttons(self) -> None:
        for code, btn in self.brush_buttons.items():
            is_selected = code == self.active_brush
            if code is None:
                border = "2px solid #38bdf8" if is_selected else "1px solid #334155"
                bg = "#2563eb" if is_selected else "#1e293b"
                btn.setStyleSheet(
                    f"background-color: {bg}; color: #ffffff; border: {border}; "
                    "border-radius: 6px; padding: 5px 10px; font-weight: 700;"
                )
            else:
                info = COLOR_INFO[code]
                border = (
                    "3px solid #38bdf8" if is_selected else "1px solid #0f172a"
                )
                btn.setStyleSheet(
                    f"background-color: {info['hex']}; color: {info['text_color']}; "
                    f"border: {border}; border-radius: 6px; padding: 5px 10px; "
                    "font-weight: 700;"
                )

    def _on_panel_grid_changed(self, face_key: str) -> None:
        """Chamado sempre que o usuário edita ou gira qualquer uma das 6 faces."""
        self.solution_panel.pause_playback()
        self._sync_state_from_panels()

    def _sync_state_from_panels(self) -> None:
        """Sincroniza o estado lógico do cubo e a visualização 3D a partir dos 6 painéis."""
        for face_key, panel in self.face_panels.items():
            self.cube_state.set_face(face_key, panel.get_grid())

        validation = CubeValidator.validate(self.cube_state)
        self.solution_panel.update_live_validation(validation)
        self.viewer_3d.set_cube_state(self.cube_state)

    def confirm_all_faces(self) -> None:
        """Marca todas as 6 faces como confirmadas."""
        for panel in self.face_panels.values():
            panel.set_confirmed(True)
        self.statusBar().showMessage(
            "Centros e orientações de todas as 6 faces foram confirmados.", 5000
        )

    def validate_and_solve(self) -> None:
        """
        Verifica se todas as faces estão confirmadas, valida a consistência
        física do cubo e calcula a solução determinística com kociemba.
        """
        self._sync_state_from_panels()

        unconfirmed = [
            FACE_NAMES_PT[f]
            for f in PANEL_DISPLAY_ORDER
            if not self.face_panels[f].is_confirmed()
        ]
        if unconfirmed:
            resp = QMessageBox.question(
                self,
                "Confirmar Centro e Orientação das Faces",
                "As seguintes faces ainda não tiveram o centro e a orientação confirmados:\n\n"
                + "\n".join(f"• {name}" for name in unconfirmed)
                + "\n\nDeseja confirmar que os centros e orientações estão "
                "corretos e prosseguir?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if resp == QMessageBox.StandardButton.Yes:
                self.confirm_all_faces()
            else:
                return

        result = CubeSolverEngine.solve(self.cube_state)
        self.solution_panel.display_solution(self.cube_state, result)

        if not result.success:
            QMessageBox.warning(
                self,
                "Estado do Cubo Inválido ou Impossível",
                "Não foi possível calcular uma solução porque o estado informado "
                "apresenta inconsistências físicas:\n\n"
                f"{result.error_message}\n\n"
                "Você pode corrigir manualmente qualquer adesivo clicando sobre ele, "
                "girar a orientação de uma foto em 90° ou carregar outra imagem sem reiniciar o aplicativo.",
            )
        else:
            if result.is_already_solved:
                self.statusBar().showMessage(
                    "O cubo já se encontra resolvido!", 6000
                )
            else:
                self.statusBar().showMessage(
                    f"Solução calculada e testada com sucesso: "
                    f"{result.move_count} movimentos ({result.notation_text})",
                    10000,
                )

    def open_camera_wizard(self) -> None:
        """Abre o Assistente de Câmera para capturar uma ou todas as 6 faces."""
        dlg = CameraCaptureDialog(
            initial_face="U",
            single_face_mode=False,
            parent=self,
        )
        if dlg.exec() == CameraCaptureDialog.DialogCode.Accepted:
            if not dlg.captured_results:
                return
            for face_key, det in dlg.captured_results.items():
                if face_key in self.face_panels and det.success:
                    self.face_panels[face_key].set_grid(
                        det.grid,
                        annotated_bgr=det.annotated_image,
                        require_confirmation=True,
                    )
            self._sync_state_from_panels()
            self.statusBar().showMessage(
                f"{len(dlg.captured_results)} face(s) capturada(s) pela câmera! "
                "Verifique a orientação e os centros antes de resolver.",
                8000,
            )

    def import_six_photos_dialog(self) -> None:
        """
        Permite selecionar até 6 fotografias de uma só vez e associá-las às
        faces correspondentes (por nome de arquivo ou na ordem padrão).
        """
        default_dir = Path.cwd() / "exemplos_faces"
        start_dir = str(default_dir if default_dir.exists() else Path.cwd())

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar as fotografias das faces do cubo (selecione até 6 imagens)",
            start_dir,
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not files:
            return

        # Se selecionou 1 imagem de planificação em cruz, extrai as 6 faces
        if len(files) == 1:
            net_res = StickerDetector.extract_net_faces(files[0])
            if net_res is not None and len(net_res) == 6:
                for face_key, det in net_res.items():
                    self.face_panels[face_key].set_grid(
                        det.grid,
                        annotated_bgr=det.annotated_image,
                        require_confirmation=True,
                    )
                self._sync_state_from_panels()
                self.statusBar().showMessage(
                    "As 6 faces foram extraídas automaticamente da imagem selecionada!",
                    7000,
                )
                return

        # Associar arquivos às faces pelo nome (ex: cima/U, frente/F, etc.) ou pela ordem
        assigned: Dict[str, str] = {}
        unassigned_files: List[str] = []

        keyword_map = {
            "U": ["cima", "_u", "up", "top"],
            "D": ["baixo", "_d", "down", "bottom"],
            "F": ["frente", "_f", "front"],
            "B": ["tras", "trás", "_b", "back"],
            "L": ["esquerda", "_l", "left"],
            "R": ["direita", "_r", "right"],
        }

        for fpath in files[:6]:
            stem_lower = Path(fpath).stem.lower()
            matched_face: Optional[str] = None
            for face_key, kw_list in keyword_map.items():
                if face_key not in assigned and any(kw in stem_lower for kw in kw_list):
                    matched_face = face_key
                    break
            if matched_face is not None:
                assigned[matched_face] = fpath
            else:
                unassigned_files.append(fpath)

        remaining_faces = [f for f in FACE_ORDER if f not in assigned]
        for fpath, face_key in zip(unassigned_files, remaining_faces):
            assigned[face_key] = fpath

        errors: List[str] = []
        for face_key, fpath in assigned.items():
            det = StickerDetector.detect_face(fpath)
            if det.success:
                self.face_panels[face_key].set_grid(
                    det.grid,
                    annotated_bgr=det.annotated_image,
                    require_confirmation=True,
                )
            else:
                errors.append(f"{FACE_NAMES_PT[face_key]}: {det.error_message}")

        self._sync_state_from_panels()
        if errors:
            QMessageBox.warning(
                self,
                "Aviso ao Carregar Imagens",
                "Algumas imagens não puderam ser processadas:\n" + "\n".join(errors),
            )
        else:
            self.statusBar().showMessage(
                f"{len(assigned)} fotografia(s) carregada(s) com sucesso. "
                "Confirme o centro e a orientação de cada face antes de resolver.",
                8000,
            )

    def import_net_image_dialog(self) -> None:
        """
        Carrega uma imagem de planificação em cruz (como cubo.png) e preenche
        automaticamente os 6 painéis das faces.
        """
        default_net = Path.cwd() / "cubo.png"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar imagem de planificação do cubo (ex: cubo.png)",
            str(default_net if default_net.exists() else Path.cwd()),
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not file_path:
            return

        results = StickerDetector.extract_net_faces(file_path)
        if results is None:
            QMessageBox.warning(
                self,
                "Planificação Inválida",
                "Não foi possível localizar as 6 faces em formato de cruz nesta imagem.\n"
                "Para fotos de uma única face, utilize o botão '📁 Foto' dentro do painel da face.",
            )
            return

        for face_key, det in results.items():
            if face_key in self.face_panels and det.success:
                self.face_panels[face_key].set_grid(
                    det.grid,
                    annotated_bgr=det.annotated_image,
                    require_confirmation=True,
                )

        self._sync_state_from_panels()
        self.statusBar().showMessage(
            "Planificação carregada com sucesso nas 6 faces! "
            "Verifique os centros/orientações e clique em 'Validar e Resolver Cubo'.",
            8000,
        )

    def load_random_scramble(self) -> None:
        """Gera um embaralhamento válido aleatório e preenche os 6 painéis."""
        self.solution_panel.pause_playback()
        cube = CubeState.solved()
        bases = ["U", "D", "F", "B", "R", "L"]
        suffixes = ["", "'", "2"]
        scramble_moves: List[str] = []
        last_base = ""
        for _ in range(18):
            b = random.choice([x for x in bases if x != last_base])
            last_base = b
            scramble_moves.append(f"{b}{random.choice(suffixes)}")

        cube.apply_sequence(scramble_moves)
        for face_key, panel in self.face_panels.items():
            panel.clear_photo_preview()
            panel.set_grid(cube.get_face(face_key), require_confirmation=False)
            panel.set_confirmed(True)

        self._sync_state_from_panels()
        self.statusBar().showMessage(
            f"Embaralhamento aplicado: {' '.join(scramble_moves)}. "
            "Clique em 'Validar e Resolver Cubo' para calcular a solução.",
            10000,
        )

    def reset_to_solved(self) -> None:
        """Restaura todas as faces para o estado resolvido padrão."""
        self.solution_panel.pause_playback()
        cube = CubeState.solved()
        for face_key, panel in self.face_panels.items():
            panel.clear_photo_preview()
            panel.set_grid(cube.get_face(face_key), require_confirmation=False)
            panel.set_confirmed(True)

        self._sync_state_from_panels()
        self.statusBar().showMessage("Cubo restaurado para o estado resolvido.", 5000)
