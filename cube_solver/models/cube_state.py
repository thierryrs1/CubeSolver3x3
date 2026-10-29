"""Representação do estado do cubo mágico 3x3x3 e operações de movimento."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional

# Ordem oficial usada pela notação Kociemba: U, R, F, D, L, B
FACE_ORDER: List[str] = ["U", "R", "F", "D", "L", "B"]

# Nomes em português brasileiro conforme o escopo
FACE_NAMES_PT: Dict[str, str] = {
    "U": "Cima (U)",
    "R": "Direita (R)",
    "F": "Frente (F)",
    "D": "Baixo (D)",
    "L": "Esquerda (L)",
    "B": "Trás (B)",
}

# Cores suportadas pelo sistema (códigos internos: W, Y, R, O, G, B)
COLOR_INFO: Dict[str, Dict[str, str]] = {
    "W": {"name": "Branco", "hex": "#F8FAFC", "text_color": "#0F172A"},
    "R": {"name": "Vermelho", "hex": "#EF4444", "text_color": "#FFFFFF"},
    "G": {"name": "Verde", "hex": "#22C55E", "text_color": "#052E16"},
    "Y": {"name": "Amarelo", "hex": "#FACC15", "text_color": "#1E293B"},
    "O": {"name": "Laranja", "hex": "#F97316", "text_color": "#FFFFFF"},
    "B": {"name": "Azul", "hex": "#2563EB", "text_color": "#FFFFFF"},
}

VALID_COLORS: List[str] = list(COLOR_INFO.keys())

# Esquema padrão ocidental (compatível também com cubo.png: U=W, R=G, F=R, D=Y, L=B, B=O)
DEFAULT_FACE_COLORS: Dict[str, str] = {
    "U": "W",
    "R": "G",
    "F": "R",
    "D": "Y",
    "L": "B",
    "B": "O",
}


def _rotate_grid_cw(grid: List[List[str]]) -> List[List[str]]:
    """Gira uma grade 3x3 em 90 graus no sentido horário."""
    return [[grid[2 - r][c] for r in range(3)] for c in range(3)]


def _rotate_grid_ccw(grid: List[List[str]]) -> List[List[str]]:
    """Gira uma grade 3x3 em 90 graus no sentido anti-horário."""
    return [[grid[r][2 - c] for r in range(3)] for c in range(3)]


def _rotate_grid_180(grid: List[List[str]]) -> List[List[str]]:
    """Gira uma grade 3x3 em 180 graus."""
    return _rotate_grid_cw(_rotate_grid_cw(grid))


class CubeState:
    """
    Representa o estado completo de um cubo mágico 3x3x3.

    Cada face ('U', 'R', 'F', 'D', 'L', 'B') contém uma matriz 3x3 de cores
    ('W', 'R', 'G', 'Y', 'O', 'B'), indexada de [0][0] (canto superior esquerdo)
    a [2][2] (canto inferior direito) olhando diretamente para a face:
      - Para U: topo é B, base é F, esquerda é L, direita é R.
      - Para D: topo é F, base é B, esquerda é L, direita é R.
      - Para F: topo é U, base é D, esquerda é L, direita é R.
      - Para B: topo é U, base é D, esquerda é R, direita é L.
      - Para L: topo é U, base é D, esquerda é B, direita é F.
      - Para R: topo é U, base é D, esquerda é F, direita é B.
    """

    def __init__(self, faces: Optional[Dict[str, List[List[str]]]] = None) -> None:
        if faces is None:
            self.faces: Dict[str, List[List[str]]] = {
                face: [[color for _ in range(3)] for _ in range(3)]
                for face, color in DEFAULT_FACE_COLORS.items()
            }
        else:
            self.faces = deepcopy(faces)

    @classmethod
    def solved(cls, center_colors: Optional[Dict[str, str]] = None) -> "CubeState":
        """Cria um cubo resolvido com as cores de centro informadas."""
        mapping = center_colors or DEFAULT_FACE_COLORS
        faces = {
            face: [[color for _ in range(3)] for _ in range(3)]
            for face, color in mapping.items()
        }
        return cls(faces)

    def copy(self) -> "CubeState":
        """Retorna uma cópia profunda do estado do cubo."""
        return CubeState(self.faces)

    def get_face(self, face: str) -> List[List[str]]:
        """Retorna uma cópia da matriz 3x3 de uma face."""
        return deepcopy(self.faces[face])

    def set_face(self, face: str, grid: List[List[str]]) -> None:
        """Define a matriz 3x3 de uma face."""
        if face not in FACE_ORDER:
            raise ValueError(f"Face inválida: {face}")
        if len(grid) != 3 or any(len(row) != 3 for row in grid):
            raise ValueError("A face deve ser uma matriz 3x3.")
        self.faces[face] = deepcopy(grid)

    def set_sticker(self, face: str, row: int, col: int, color: str) -> None:
        """Define a cor de um adesivo específico."""
        if face not in FACE_ORDER:
            raise ValueError(f"Face inválida: {face}")
        if color not in VALID_COLORS:
            raise ValueError(f"Cor inválida: {color}")
        self.faces[face][row][col] = color

    def rotate_face_orientation(self, face: str, clockwise: bool = True) -> None:
        """
        Gira apenas os adesivos de uma face em 90 graus (para corrigir a
        orientação de uma foto carregada sem afetar as faces vizinhas).
        """
        if face not in FACE_ORDER:
            raise ValueError(f"Face inválida: {face}")
        if clockwise:
            self.faces[face] = _rotate_grid_cw(self.faces[face])
        else:
            self.faces[face] = _rotate_grid_ccw(self.faces[face])

    def get_center_map(self) -> Dict[str, str]:
        """Retorna o mapa {cor_do_centro: letra_da_face}."""
        return {self.faces[face][1][1]: face for face in FACE_ORDER}

    def is_solved(self) -> bool:
        """Verifica se cada face possui todos os 9 adesivos da mesma cor e 6 centros distintos."""
        centers = set()
        for face in FACE_ORDER:
            grid = self.faces[face]
            center = grid[1][1]
            centers.add(center)
            for r in range(3):
                for c in range(3):
                    if grid[r][c] != center:
                        return False
        return len(centers) == 6

    def _move_U(self) -> None:
        """Gira a face U 90 graus no sentido horário."""
        self.faces["U"] = _rotate_grid_cw(self.faces["U"])
        temp = self.faces["F"][0][:]
        self.faces["F"][0] = self.faces["R"][0][:]
        self.faces["R"][0] = self.faces["B"][0][:]
        self.faces["B"][0] = self.faces["L"][0][:]
        self.faces["L"][0] = temp

    def _move_D(self) -> None:
        """Gira a face D 90 graus no sentido horário."""
        self.faces["D"] = _rotate_grid_cw(self.faces["D"])
        temp = self.faces["F"][2][:]
        self.faces["F"][2] = self.faces["L"][2][:]
        self.faces["L"][2] = self.faces["B"][2][:]
        self.faces["B"][2] = self.faces["R"][2][:]
        self.faces["R"][2] = temp

    def _move_F(self) -> None:
        """Gira a face F 90 graus no sentido horário."""
        self.faces["F"] = _rotate_grid_cw(self.faces["F"])
        temp = self.faces["U"][2][:]
        # L coluna direita (de baixo para cima) -> U linha inferior (da esquerda para a direita)
        self.faces["U"][2] = [
            self.faces["L"][2][2],
            self.faces["L"][1][2],
            self.faces["L"][0][2],
        ]
        # D linha superior -> L coluna direita
        for i in range(3):
            self.faces["L"][i][2] = self.faces["D"][0][i]
        # R coluna esquerda (de baixo para cima) -> D linha superior
        self.faces["D"][0] = [
            self.faces["R"][2][0],
            self.faces["R"][1][0],
            self.faces["R"][0][0],
        ]
        # temp (antigo U[2]) -> R coluna esquerda
        for i in range(3):
            self.faces["R"][i][0] = temp[i]

    def _move_B(self) -> None:
        """Gira a face B 90 graus no sentido horário."""
        self.faces["B"] = _rotate_grid_cw(self.faces["B"])
        temp = self.faces["U"][0][:]
        # R coluna direita -> U linha superior
        self.faces["U"][0] = [
            self.faces["R"][0][2],
            self.faces["R"][1][2],
            self.faces["R"][2][2],
        ]
        # D linha inferior (invertida) -> R coluna direita
        for i in range(3):
            self.faces["R"][i][2] = self.faces["D"][2][2 - i]
        # L coluna esquerda -> D linha inferior
        self.faces["D"][2] = [
            self.faces["L"][0][0],
            self.faces["L"][1][0],
            self.faces["L"][2][0],
        ]
        # temp (antigo U[0], invertido) -> L coluna esquerda
        for i in range(3):
            self.faces["L"][i][0] = temp[2 - i]

    def _move_R(self) -> None:
        """Gira a face R 90 graus no sentido horário."""
        self.faces["R"] = _rotate_grid_cw(self.faces["R"])
        temp = [self.faces["U"][i][2] for i in range(3)]
        for i in range(3):
            self.faces["U"][i][2] = self.faces["F"][i][2]
            self.faces["F"][i][2] = self.faces["D"][i][2]
            self.faces["D"][i][2] = self.faces["B"][2 - i][0]
            self.faces["B"][2 - i][0] = temp[i]

    def _move_L(self) -> None:
        """Gira a face L 90 graus no sentido horário."""
        self.faces["L"] = _rotate_grid_cw(self.faces["L"])
        temp = [self.faces["U"][i][0] for i in range(3)]
        for i in range(3):
            self.faces["U"][i][0] = self.faces["B"][2 - i][2]
            self.faces["B"][2 - i][2] = self.faces["D"][i][0]
            self.faces["D"][i][0] = self.faces["F"][i][0]
            self.faces["F"][i][0] = temp[i]

    def apply_move(self, move: str) -> None:
        """
        Aplica um único movimento na notação padrão (ex.: 'U', "U'", 'U2', 'R', "F'", etc.).
        """
        move = move.strip()
        if not move:
            return
        base = move[0].upper()
        suffix = move[1:]

        move_map = {
            "U": self._move_U,
            "D": self._move_D,
            "F": self._move_F,
            "B": self._move_B,
            "R": self._move_R,
            "L": self._move_L,
        }
        if base not in move_map:
            raise ValueError(f"Movimento desconhecido: '{move}'")

        func = move_map[base]
        if suffix == "":
            func()
        elif suffix == "'":
            func()
            func()
            func()
        elif suffix == "2":
            func()
            func()
        else:
            raise ValueError(f"Modificador de movimento inválido em: '{move}'")

    def apply_sequence(self, sequence: str | List[str]) -> None:
        """Aplica uma sequência de movimentos separada por espaços ou em lista."""
        if isinstance(sequence, str):
            moves = [m for m in sequence.strip().split() if m]
        else:
            moves = [m.strip() for m in sequence if m.strip()]
        for move in moves:
            self.apply_move(move)
