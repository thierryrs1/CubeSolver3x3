"""Widget PySide6 para renderizar e animar o cubo mágico em 3D com Three.js."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget

from cube_solver.models.cube_state import CubeState


class Cube3DViewerWidget(QWidget):
    """
    Encapsula um QWebEngineView carregando a cena Three.js interativa (`cube3d.html`)
    e expõe métodos Python para atualizar o estado do cubo e animar movimentos.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._is_loaded = False
        self._pending_state: Optional[CubeState] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView(self)
        self.web_view.setMinimumSize(360, 320)
        layout.addWidget(self.web_view)

        html_path = Path(__file__).resolve().parent / "assets" / "cube3d.html"
        self.web_view.loadFinished.connect(self._on_load_finished)
        self.web_view.load(QUrl.fromLocalFile(str(html_path)))

    def _on_load_finished(self, ok: bool) -> None:
        self._is_loaded = ok
        if ok and self._pending_state is not None:
            self.set_cube_state(self._pending_state)

    def set_cube_state(self, state: CubeState, banner_text: str = "") -> None:
        """Atualiza imediatamente todos os 54 adesivos do cubo 3D."""
        self._pending_state = state.copy()
        if not self._is_loaded:
            return
        faces_json = json.dumps(state.faces)
        banner_json = json.dumps(banner_text)
        js = f"if (window.setCubeState) window.setCubeState({faces_json}, {banner_json});"
        self.web_view.page().runJavaScript(js)

    def animate_move(
        self,
        move: str,
        target_state: CubeState,
        duration_ms: int = 380,
    ) -> None:
        """Executa a animação 3D de um giro de face e sincroniza com target_state."""
        self._pending_state = target_state.copy()
        if not self._is_loaded:
            return
        move_json = json.dumps(move)
        faces_json = json.dumps(target_state.faces)
        js = (
            f"if (window.animateMove) "
            f"window.animateMove({move_json}, {faces_json}, {int(duration_ms)});"
        )
        self.web_view.page().runJavaScript(js)

