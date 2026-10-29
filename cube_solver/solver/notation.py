"""Conversão entre CubeState e notação Kociemba (54 caracteres) + explicação dos movimentos."""

from __future__ import annotations

from typing import Dict, List, Optional

from cube_solver.models.cube_state import DEFAULT_FACE_COLORS, FACE_ORDER, CubeState

# Explicações detalhadas em português brasileiro para cada movimento
MOVE_EXPLANATIONS_PT: Dict[str, str] = {
    "U": "Gire a face de Cima (U) 90° no sentido horário (olhando de cima).",
    "U'": "Gire a face de Cima (U) 90° no sentido anti-horário (olhando de cima).",
    "U2": "Gire a face de Cima (U) 180° (meia-volta).",
    "D": "Gire a face de Baixo (D) 90° no sentido horário (olhando de baixo).",
    "D'": "Gire a face de Baixo (D) 90° no sentido anti-horário (olhando de baixo).",
    "D2": "Gire a face de Baixo (D) 180° (meia-volta).",
    "F": "Gire a face da Frente (F) 90° no sentido horário (olhando de frente).",
    "F'": "Gire a face da Frente (F) 90° no sentido anti-horário (olhando de frente).",
    "F2": "Gire a face da Frente (F) 180° (meia-volta).",
    "B": "Gire a face de Trás (B) 90° no sentido horário (olhando por trás).",
    "B'": "Gire a face de Trás (B) 90° no sentido anti-horário (olhando por trás).",
    "B2": "Gire a face de Trás (B) 180° (meia-volta).",
    "R": "Gire a face da Direita (R) 90° no sentido horário (olhando pela direita, para cima/trás).",
    "R'": "Gire a face da Direita (R) 90° no sentido anti-horário (olhando pela direita, para frente/baixo).",
    "R2": "Gire a face da Direita (R) 180° (meia-volta).",
    "L": "Gire a face da Esquerda (L) 90° no sentido horário (olhando pela esquerda, para frente/baixo).",
    "L'": "Gire a face da Esquerda (L) 90° no sentido anti-horário (olhando pela esquerda, para cima/trás).",
    "L2": "Gire a face da Esquerda (L) 180° (meia-volta).",
}


def state_to_kociemba(state: CubeState) -> str:
    """
    Converte um CubeState para a string de 54 caracteres na ordem exigida
    pela biblioteca kociemba: U1..U9, R1..R9, F1..F9, D1..D9, L1..L9, B1..B9.

    O mapeamento de cor -> letra da face ('U', 'R', 'F', 'D', 'L', 'B') é
    determinado dinamicamente pelos 6 centros atuais do cubo.
    """
    center_to_face: Dict[str, str] = {}
    for face in FACE_ORDER:
        center_color = state.faces[face][1][1]
        if center_color in center_to_face:
            raise ValueError(
                f"Centros duplicados detectados para a cor '{center_color}'."
            )
        center_to_face[center_color] = face

    chars: List[str] = []
    for face in FACE_ORDER:
        grid = state.faces[face]
        for r in range(3):
            for c in range(3):
                color = grid[r][c]
                if color not in center_to_face:
                    raise ValueError(
                        f"A cor '{color}' na face '{face}' não corresponde a nenhum centro."
                    )
                chars.append(center_to_face[color])

    result = "".join(chars)
    if len(result) != 54:
        raise ValueError(f"String Kociemba inválida com tamanho {len(result)}.")
    return result


def kociemba_to_state(
    kociemba_str: str,
    face_to_color: Optional[Dict[str, str]] = None,
) -> CubeState:
    """
    Converte uma string Kociemba de 54 caracteres ('U', 'R', 'F', 'D', 'L', 'B')
    em uma instância de CubeState.
    """
    cleaned = kociemba_str.strip()
    if len(cleaned) != 54:
        raise ValueError(
            f"A string Kociemba deve conter exatamente 54 caracteres (recebido: {len(cleaned)})."
        )
    allowed = set(FACE_ORDER)
    if any(ch not in allowed for ch in cleaned):
        raise ValueError(
            "A string Kociemba deve conter apenas os caracteres U, R, F, D, L e B."
        )

    mapping = face_to_color or DEFAULT_FACE_COLORS
    faces: Dict[str, List[List[str]]] = {}
    idx = 0
    for face in FACE_ORDER:
        grid: List[List[str]] = []
        for _ in range(3):
            row: List[str] = []
            for _ in range(3):
                face_letter = cleaned[idx]
                row.append(mapping[face_letter])
                idx += 1
            grid.append(row)
        faces[face] = grid

    return CubeState(faces)


def explain_move(move: str) -> str:
    """Retorna a explicação em português de como executar um movimento."""
    m = move.strip()
    return MOVE_EXPLANATIONS_PT.get(
        m, f"Execute o movimento {m} na face correspondente."
    )
