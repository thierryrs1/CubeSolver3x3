"""Testes automatizados para a interface gráfica PySide6 (MainWindow e painéis)."""

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from cube_solver.ui.main_window import MainWindow  # noqa: E402
from cube_solver.vision.detector import StickerDetector  # noqa: E402


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Garante instância única de QApplication para os testes."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app  # type: ignore[return-value]


def test_main_window_Manual_scramble_and_solve(qapp: QApplication) -> None:
    """Testa embaralhar manualmente na interface, resolver e avançar/voltar passos."""
    win = MainWindow()
    win.load_random_scramble()
    win.confirm_all_faces()
    win.validate_and_solve()

    sol_panel = win.solution_panel
    assert len(sol_panel._moves) > 0
    assert sol_panel._current_step == 0

    # Avançar um passo
    sol_panel.step_forward()
    assert sol_panel._current_step == 1

    # Voltar um passo
    sol_panel.step_backward()
    assert sol_panel._current_step == 0

    # Avançar até o fim e verificar que o cubo termina resolvido
    while sol_panel._current_step < len(sol_panel._moves):
        sol_panel.step_forward()
    assert sol_panel._current_state.is_solved() is True

    # Reiniciar sequência
    sol_panel.restart_sequence()
    assert sol_panel._current_step == 0
    win.close()


def test_main_window_load_net_and_rotate_orientation(qapp: QApplication) -> None:
    """Testa carregar as faces de cubo.png nos painéis, girar orientação e resolver."""
    win = MainWindow()
    net_path = Path(__file__).resolve().parent.parent / "cubo.png"
    results = StickerDetector.extract_net_faces(net_path)
    assert results is not None

    for face_key, det in results.items():
        win.face_panels[face_key].apply_detection_result(det)

    # Girar a face F 90° horário e depois 90° anti-horário para testar correção de orientação
    win.face_panels["F"].rotate_orientation(clockwise=True)
    win.face_panels["F"].rotate_orientation(clockwise=False)

    win.confirm_all_faces()
    win.validate_and_solve()
    assert len(win.solution_panel._moves) > 0
    win.close()

