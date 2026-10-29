"""Painel de validação, exibição da solução Kociemba e controle de animação 3D passo a passo."""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cube_solver.models.cube_state import COLOR_INFO, VALID_COLORS, CubeState
from cube_solver.solver.kociemba_solver import SolutionResult
from cube_solver.solver.notation import explain_move
from cube_solver.validation.validator import ValidationResult


def invert_move(move: str) -> str:
    """Retorna o movimento inverso para quando o usuário clica em 'Voltar'."""
    m = move.strip()
    if not m:
        return ""
    base = m[0]
    suffix = m[1:]
    if suffix == "":
        return f"{base}'"
    if suffix == "'":
        return base
    return m  # '2' é seu próprio inverso


class SolutionPanel(QWidget):
    """
    Painel direito inferior que exibe:
      - Contadores em tempo real das 6 cores (ex.: Branco 9/9);
      - Diagnóstico de validação física e mensagens de erro claras;
      - Sequência completa calculada pelo algoritmo Kociemba;
      - Controles de reprodução 3D (Reiniciar, Voltar, Executar/Pausar, Avançar);
      - Explicação detalhada em português de cada movimento.
    """

    request_3d_sync = Signal(CubeState, str)
    request_3d_animate = Signal(str, CubeState, int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._initial_state: CubeState = CubeState.solved()
        self._current_state: CubeState = CubeState.solved()
        self._moves: List[str] = []
        self._current_step: int = 0  # 0 = estado inicial, len(_moves) = resolvido

        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self._on_timer_tick)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. Contadores de cores em tempo real
        counts_group = QGroupBox("Contagem de Adesivos por Cor (Meta: 9 de cada)")
        counts_layout = QHBoxLayout(counts_group)
        counts_layout.setSpacing(6)

        self.color_badges: Dict[str, QLabel] = {}
        for col in VALID_COLORS:
            info = COLOR_INFO[col]
            lbl = QLabel(f"{info['name']}: 9/9")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"background-color: {info['hex']}; color: {info['text_color']}; "
                "padding: 4px 6px; border-radius: 6px; font-weight: 700; font-size: 11px;"
            )
            counts_layout.addWidget(lbl)
            self.color_badges[col] = lbl

        layout.addWidget(counts_group)

        # 2. Status de Validação e Notação Kociemba
        status_group = QGroupBox("Diagnóstico de Validação e Solução")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(6)

        self.validation_label = QLabel(
            "✔ Cubo inicializado. Edite as cores, carregue as 6 fotos ou use a câmera."
        )
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet(
            "background-color: #0f172a; color: #34d399; padding: 8px 10px; "
            "border-radius: 6px; border: 1px solid #059669; font-weight: 600;"
        )
        status_layout.addWidget(self.validation_label)

        self.sequence_label = QLabel("Sequência de Solução: —")
        self.sequence_label.setWordWrap(True)
        self.sequence_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.sequence_label.setStyleSheet(
            "color: #38bdf8; font-weight: 700; font-size: 13px; padding: 2px 0;"
        )
        status_layout.addWidget(self.sequence_label)

        self.kociemba_label = QLabel("Notação Kociemba (54 faces): —")
        self.kociemba_label.setWordWrap(True)
        self.kociemba_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.kociemba_label.setStyleSheet(
            "color: #64748b; font-family: Consolas, monospace; font-size: 11px;"
        )
        status_layout.addWidget(self.kociemba_label)

        layout.addWidget(status_group)

        # 3. Controles de Reprodução Passo a Passo e Explicação do Movimento Atual
        playback_group = QGroupBox("Controle Passo a Passo e Explicação dos Movimentos")
        pb_layout = QVBoxLayout(playback_group)
        pb_layout.setSpacing(8)

        # Destaque do passo atual
        self.current_move_banner = QLabel("Nenhum movimento em execução")
        self.current_move_banner.setWordWrap(True)
        self.current_move_banner.setStyleSheet(
            "background-color: #1e293b; color: #f8fafc; padding: 8px 12px; "
            "border-radius: 8px; border-left: 4px solid #38bdf8; font-size: 13px;"
        )
        pb_layout.addWidget(self.current_move_banner)

        # Botões de controle: Reiniciar, Voltar, Play/Pause, Avançar, Velocidade
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(6)

        self.btn_restart = QPushButton("⏮ Reiniciar")
        self.btn_restart.clicked.connect(self.restart_sequence)
        ctrl_row.addWidget(self.btn_restart)

        self.btn_prev = QPushButton("⏪ Voltar")
        self.btn_prev.clicked.connect(self.step_backward)
        ctrl_row.addWidget(self.btn_prev)

        self.btn_play = QPushButton("▶ Executar")
        self.btn_play.setObjectName("primaryButton")
        self.btn_play.clicked.connect(self.toggle_playback)
        ctrl_row.addWidget(self.btn_play)

        self.btn_next = QPushButton("⏩ Avançar")
        self.btn_next.clicked.connect(self.step_forward)
        ctrl_row.addWidget(self.btn_next)

        ctrl_row.addSpacing(8)
        ctrl_row.addWidget(QLabel("Velocidade:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItem("Lenta (900 ms)", userData=900)
        self.speed_combo.addItem("Normal (520 ms)", userData=520)
        self.speed_combo.addItem("Rápida (280 ms)", userData=280)
        self.speed_combo.setCurrentIndex(1)
        ctrl_row.addWidget(self.speed_combo)

        pb_layout.addLayout(ctrl_row)

        # Lista de passos numerados com explicação
        self.steps_list = QListWidget()
        self.steps_list.setMinimumHeight(130)
        pb_layout.addWidget(self.steps_list)

        layout.addWidget(playback_group)
        self._update_controls_enabled()

    def update_live_validation(self, validation: ValidationResult) -> None:
        """Atualiza os contadores de cores e o status de validação ao editar adesivos."""
        for col in VALID_COLORS:
            info = COLOR_INFO[col]
            qty = validation.color_counts.get(col, 0)
            badge = self.color_badges[col]
            badge.setText(f"{info['name']}: {qty}/9")
            if qty == 9:
                badge.setStyleSheet(
                    f"background-color: {info['hex']}; color: {info['text_color']}; "
                    "padding: 4px 6px; border-radius: 6px; font-weight: 700; font-size: 11px; "
                    "border: 2px solid #10b981;"
                )
            else:
                badge.setStyleSheet(
                    f"background-color: {info['hex']}; color: {info['text_color']}; "
                    "padding: 4px 6px; border-radius: 6px; font-weight: 700; font-size: 11px; "
                    "border: 2px solid #ef4444;"
                )

        if validation.is_valid:
            self.validation_label.setText(
                "✔ Estado do cubo fisicamente válido! Clique em "
                "'Validar e Resolver Cubo' para calcular a solução."
            )
            self.validation_label.setStyleSheet(
                "background-color: #064e3b; color: #a7f3d0; padding: 8px 10px; "
                "border-radius: 6px; border: 1px solid #10b981; font-weight: 600;"
            )
        else:
            self.validation_label.setText(f"⚠ {validation.summary}")
            self.validation_label.setStyleSheet(
                "background-color: #450a0a; color: #fecaca; padding: 8px 10px; "
                "border-radius: 6px; border: 1px solid #ef4444; font-weight: 600;"
            )

    def display_solution(
        self, initial_state: CubeState, result: SolutionResult
    ) -> None:
        """Exibe a solução calculada pelo motor Kociemba e prepara a animação 3D."""
        self.pause_playback()
        if result.validation is not None:
            self.update_live_validation(result.validation)

        if not result.success:
            self._moves = []
            self._current_step = 0
            self.steps_list.clear()
            self.sequence_label.setText("Sequência de Solução: Estado Inválido")
            self.validation_label.setText(f"❌ {result.error_message}")
            self.validation_label.setStyleSheet(
                "background-color: #450a0a; color: #fecaca; padding: 8px 10px; "
                "border-radius: 6px; border: 1px solid #ef4444; font-weight: 600;"
            )
            self.current_move_banner.setText(
                "Corrija as cores destacadas ou a orientação das fotos e tente novamente."
            )
            self._update_controls_enabled()
            return

        self._initial_state = initial_state.copy()
        self._current_state = initial_state.copy()
        self._moves = list(result.moves)
        self._current_step = 0

        self.kociemba_label.setText(
            f"Notação Kociemba (54 faces): {result.kociemba_string}"
        )

        self.steps_list.clear()
        if result.is_already_solved:
            self.validation_label.setText(
                "🎉 O cubo já está completamente resolvido! Nenhum movimento é necessário."
            )
            self.sequence_label.setText("Sequência de Solução: 0 movimentos (Resolvido)")
            self.current_move_banner.setText("Cubo resolvido (0 passos).")
            self._update_controls_enabled()
            return

        self.validation_label.setText(
            f"✔ Solução válida calculada e verificada com sucesso em {result.move_count} movimentos!"
        )
        self.sequence_label.setText(
            f"Solução ({result.move_count} passos): {result.notation_text}"
        )

        for idx, move, desc in result.get_step_descriptions():
            item = QListWidgetItem(f"Passo {idx:02d}/{result.move_count:02d}:  {move:<3} —  {desc}")
            self.steps_list.addItem(item)

        self.current_move_banner.setText(
            f"Pronto para iniciar ({len(self._moves)} movimentos). "
            "Use '▶ Executar' ou '⏩ Avançar' para ver cada giro em 3D."
        )
        self._update_controls_enabled()
        self.request_3d_sync.emit(self._current_state, "Passo 0/" + str(len(self._moves)))

    def _get_anim_duration(self) -> int:
        val = self.speed_combo.currentData()
        return int(val) if val is not None else 520

    def step_forward(self) -> None:
        """Avança um movimento na sequência da solução e anima o cubo 3D."""
        if self._current_step >= len(self._moves):
            self.pause_playback()
            return

        move = self._moves[self._current_step]
        self._current_state.apply_move(move)
        self._current_step += 1

        self.steps_list.setCurrentRow(self._current_step - 1)
        desc = explain_move(move)
        self.current_move_banner.setText(
            f"Passo {self._current_step}/{len(self._moves)} — Movimento [{move}]: {desc}"
        )

        dur = max(160, int(self._get_anim_duration() * 0.78))
        self.request_3d_animate.emit(move, self._current_state, dur)
        self._update_controls_enabled()

        if self._current_step >= len(self._moves):
            self.pause_playback()
            self.current_move_banner.setText(
                f"🎉 Cubo Resolvido! Todos os {len(self._moves)} movimentos foram concluídos."
            )

    def step_backward(self) -> None:
        """Volta um movimento na sequência da solução com animação reversa."""
        self.pause_playback()
        if self._current_step <= 0:
            return

        self._current_step -= 1
        last_move = self._moves[self._current_step]
        inv_move = invert_move(last_move)
        self._current_state.apply_move(inv_move)

        if self._current_step > 0:
            prev_move = self._moves[self._current_step - 1]
            self.steps_list.setCurrentRow(self._current_step - 1)
            self.current_move_banner.setText(
                f"Voltou para Passo {self._current_step}/{len(self._moves)} "
                f"(desfez {last_move}) — Anterior [{prev_move}]: {explain_move(prev_move)}"
            )
        else:
            self.steps_list.clearSelection()
            self.current_move_banner.setText(
                f"Posição Inicial (Passo 0/{len(self._moves)}). Pronto para iniciar."
            )

        dur = max(160, int(self._get_anim_duration() * 0.78))
        self.request_3d_animate.emit(inv_move, self._current_state, dur)
        self._update_controls_enabled()

    def restart_sequence(self) -> None:
        """Reinicia a animação 3D de volta para o estado inicial embaralhado."""
        self.pause_playback()
        if not self._moves:
            return
        self._current_step = 0
        self._current_state = self._initial_state.copy()
        self.steps_list.clearSelection()
        self.current_move_banner.setText(
            f"Sequência reiniciada (Passo 0/{len(self._moves)})."
        )
        self.request_3d_sync.emit(
            self._current_state, f"Passo 0/{len(self._moves)}"
        )
        self._update_controls_enabled()

    def toggle_playback(self) -> None:
        """Alterna entre reprodução automática e pausa."""
        if self.play_timer.isActive():
            self.pause_playback()
        else:
            if self._current_step >= len(self._moves):
                self.restart_sequence()
            interval = self._get_anim_duration()
            self.btn_play.setText("⏸ Pausar")
            self.step_forward()
            if self._current_step < len(self._moves):
                self.play_timer.start(interval)

    def pause_playback(self) -> None:
        """Pausa a reprodução automática."""
        if self.play_timer.isActive():
            self.play_timer.stop()
        self.btn_play.setText("▶ Executar")

    def _on_timer_tick(self) -> None:
        if self._current_step < len(self._moves):
            self.step_forward()
        else:
            self.pause_playback()

    def _update_controls_enabled(self) -> None:
        has_moves = len(self._moves) > 0
        self.btn_restart.setEnabled(has_moves and self._current_step > 0)
        self.btn_prev.setEnabled(has_moves and self._current_step > 0)
        self.btn_play.setEnabled(has_moves)
        self.btn_next.setEnabled(has_moves and self._current_step < len(self._moves))
