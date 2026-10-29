"""Ponto de entrada do aplicativo desktop CubeSolver."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from cube_solver.ui.main_window import MainWindow


def main() -> int:
    """Inicializa e executa a aplicação gráfica PySide6."""
    app = QApplication(sys.argv)
    app.setApplicationName("CubeSolver")
    app.setOrganizationName("CubeSolver")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

