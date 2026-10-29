"""Validação completa de cores, peças de canto/aresta, orientação e paridade do cubo."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from cube_solver.models.cube_state import (
    COLOR_INFO,
    FACE_NAMES_PT,
    FACE_ORDER,
    VALID_COLORS,
    CubeState,
)

# Definição dos 8 cantos em sentido horário ao redor de cada vértice:
# (nome, [(face, linha, coluna), ...], (face_1, face_2, face_3))
CORNER_DEFINITIONS: List[Tuple[str, List[Tuple[str, int, int]], Tuple[str, str, str]]] = [
    ("URF", [("U", 2, 2), ("R", 0, 0), ("F", 0, 2)], ("U", "R", "F")),
    ("UFL", [("U", 2, 0), ("F", 0, 0), ("L", 0, 2)], ("U", "F", "L")),
    ("ULB", [("U", 0, 0), ("L", 0, 0), ("B", 0, 2)], ("U", "L", "B")),
    ("UBR", [("U", 0, 2), ("B", 0, 0), ("R", 0, 2)], ("U", "B", "R")),
    ("DFR", [("D", 0, 2), ("F", 2, 2), ("R", 2, 0)], ("D", "F", "R")),
    ("DLF", [("D", 0, 0), ("L", 2, 2), ("F", 2, 0)], ("D", "L", "F")),
    ("DBL", [("D", 2, 0), ("B", 2, 2), ("L", 2, 0)], ("D", "B", "L")),
    ("DRB", [("D", 2, 2), ("R", 2, 2), ("B", 2, 0)], ("D", "R", "B")),
]

# Definição das 12 arestas:
# (nome, [(face_primaria, l, c), (face_secundaria, l, c)], (face_1, face_2))
EDGE_DEFINITIONS: List[Tuple[str, List[Tuple[str, int, int]], Tuple[str, str]]] = [
    ("UR", [("U", 1, 2), ("R", 0, 1)], ("U", "R")),
    ("UF", [("U", 2, 1), ("F", 0, 1)], ("U", "F")),
    ("UL", [("U", 1, 0), ("L", 0, 1)], ("U", "L")),
    ("UB", [("U", 0, 1), ("B", 0, 1)], ("U", "B")),
    ("DR", [("D", 1, 2), ("R", 2, 1)], ("D", "R")),
    ("DF", [("D", 0, 1), ("F", 2, 1)], ("D", "F")),
    ("DL", [("D", 1, 0), ("L", 2, 1)], ("D", "L")),
    ("DB", [("D", 2, 1), ("B", 2, 1)], ("D", "B")),
    ("FR", [("F", 1, 2), ("R", 1, 0)], ("F", "R")),
    ("FL", [("F", 1, 0), ("L", 1, 2)], ("F", "L")),
    ("BL", [("B", 1, 2), ("L", 1, 0)], ("B", "L")),
    ("BR", [("B", 1, 0), ("R", 1, 2)], ("B", "R")),
]


@dataclass
class ValidationResult:
    """Resultado detalhado da validação de um estado do cubo."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    color_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def summary(self) -> str:
        """Retorna um resumo amigável em português do resultado da validação."""
        if self.is_valid:
            return "Estado do cubo válido e fisicamente consistente."
        return "\n".join(f"• {err}" for err in self.errors)


def _permutation_parity(perm: List[int]) -> int:
    """Calcula a paridade (0 para par, 1 para ímpar) de uma permutação."""
    inversions = 0
    n = len(perm)
    for i in range(n):
        for j in range(i + 1, n):
            if perm[i] > perm[j]:
                inversions += 1
    return inversions % 2


class CubeValidator:
    """Validador determinístico das propriedades físicas e combinatórias de um cubo 3x3x3."""

    @staticmethod
    def validate(state: CubeState) -> ValidationResult:
        """
        Executa todas as validações exigidas pelo escopo:
          1. Presença das 6 faces 3x3 com cores válidas.
          2. Contagem exata de 9 adesivos para cada uma das 6 cores.
          3. Seis centros com cores distintas.
          4. Consistência das 8 peças de canto e sua quiralidade.
          5. Consistência das 12 peças de aresta.
          6. Orientação total dos cantos (soma divisível por 3).
          7. Orientação total das arestas (soma divisível por 2).
          8. Paridade global de permutação (paridade dos cantos == paridade das arestas).
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Verificar estrutura e cores válidas
        all_stickers: List[str] = []
        for face in FACE_ORDER:
            if face not in state.faces:
                errors.append(f"A face '{FACE_NAMES_PT.get(face, face)}' não foi preenchida.")
                continue
            grid = state.faces[face]
            if len(grid) != 3 or any(len(row) != 3 for row in grid):
                errors.append(f"A face '{FACE_NAMES_PT.get(face, face)}' não possui formato 3x3.")
                continue
            for r in range(3):
                for c in range(3):
                    col = grid[r][c]
                    if col not in VALID_COLORS:
                        errors.append(
                            f"Cor inválida '{col}' na face {FACE_NAMES_PT[face]} "
                            f"(linha {r + 1}, coluna {c + 1})."
                        )
                    else:
                        all_stickers.append(col)

        counts = Counter(all_stickers)
        color_counts = {c: counts.get(c, 0) for c in VALID_COLORS}

        if errors:
            return ValidationResult(False, errors, warnings, color_counts)

        # 2. Verificar contagem de 9 adesivos de cada cor
        wrong_counts: List[str] = []
        for col in VALID_COLORS:
            qty = color_counts[col]
            if qty != 9:
                col_name = COLOR_INFO[col]["name"]
                wrong_counts.append(f"{col_name}: {qty}/9")
        if wrong_counts:
            errors.append(
                "Quantidade incorreta de adesivos por cor (cada cor deve aparecer exatamente "
                f"9 vezes): {', '.join(wrong_counts)}."
            )

        # 3. Verificar se os 6 centros possuem cores distintas
        center_colors: Dict[str, str] = {}
        center_seen: Dict[str, str] = {}
        for face in FACE_ORDER:
            c_col = state.faces[face][1][1]
            center_colors[face] = c_col
            if c_col in center_seen:
                col_name = COLOR_INFO[c_col]["name"]
                prev_face = FACE_NAMES_PT[center_seen[c_col]]
                curr_face = FACE_NAMES_PT[face]
                errors.append(
                    f"Centro duplicado: a cor {col_name} está no centro de "
                    f"'{prev_face}' e de '{curr_face}'. Cada face deve ter um centro único."
                )
            else:
                center_seen[c_col] = face

        if errors:
            return ValidationResult(False, errors, warnings, color_counts)

        # Mapa de cor -> face (U, R, F, D, L, B)
        color_to_face: Dict[str, str] = {col: face for face, col in center_colors.items()}

        # 4. Validar as 8 peças de canto (existência, unicidade, quiralidade e orientação)
        valid_corner_map: Dict[frozenset[str], Tuple[int, Tuple[str, str, str]]] = {
            frozenset(target): (idx, target)
            for idx, (_, _, target) in enumerate(CORNER_DEFINITIONS)
        }

        corner_perm: List[int] = []
        corner_orient_sum = 0
        seen_corners: Dict[int, str] = {}

        for pos_name, coords, _ in CORNER_DEFINITIONS:
            actual_faces = tuple(
                color_to_face[state.faces[f][r][c]] for (f, r, c) in coords
            )
            actual_colors_pt = [
                COLOR_INFO[state.faces[f][r][c]]["name"] for (f, r, c) in coords
            ]
            key = frozenset(actual_faces)

            if key not in valid_corner_map:
                errors.append(
                    f"Peça de canto inválida na posição {pos_name} "
                    f"({' / '.join(actual_colors_pt)}): combinação de cores impossível."
                )
                continue

            corner_idx, target_triple = valid_corner_map[key]
            if corner_idx in seen_corners:
                errors.append(
                    f"Peça de canto duplicada ({' / '.join(actual_colors_pt)}) "
                    f"nas posições {seen_corners[corner_idx]} e {pos_name}."
                )
                continue
            seen_corners[corner_idx] = pos_name
            corner_perm.append(corner_idx)

            # Determinar orientação (0, 1 ou 2) e verificar quiralidade (sentido horário)
            # O adesivo de referência (U ou D) está sempre em target_triple[0]
            ref_face = target_triple[0]
            ori = actual_faces.index(ref_face)
            # Rotacionando actual_faces a partir de ori, deve coincidir com target_triple
            rotated = actual_faces[ori:] + actual_faces[:ori]
            if rotated != target_triple:
                errors.append(
                    f"Quiralidade inválida no canto {pos_name} ({' / '.join(actual_colors_pt)}): "
                    "os adesivos dessa peça estão espelhados ou os centros das faces estão "
                    "em um esquema incompatível."
                )
            else:
                corner_orient_sum += ori

        # 5. Validar as 12 peças de aresta (existência, unicidade e orientação)
        valid_edge_map: Dict[frozenset[str], Tuple[int, Tuple[str, str]]] = {
            frozenset(target): (idx, target)
            for idx, (_, _, target) in enumerate(EDGE_DEFINITIONS)
        }

        edge_perm: List[int] = []
        edge_orient_sum = 0
        seen_edges: Dict[int, str] = {}

        for pos_name, coords, _ in EDGE_DEFINITIONS:
            actual_faces = tuple(
                color_to_face[state.faces[f][r][c]] for (f, r, c) in coords
            )
            actual_colors_pt = [
                COLOR_INFO[state.faces[f][r][c]]["name"] for (f, r, c) in coords
            ]
            key = frozenset(actual_faces)

            if key not in valid_edge_map:
                errors.append(
                    f"Peça de aresta inválida na posição {pos_name} "
                    f"({' / '.join(actual_colors_pt)}): combinação de cores impossível."
                )
                continue

            edge_idx, target_pair = valid_edge_map[key]
            if edge_idx in seen_edges:
                errors.append(
                    f"Peça de aresta duplicada ({' / '.join(actual_colors_pt)}) "
                    f"nas posições {seen_edges[edge_idx]} e {pos_name}."
                )
                continue
            seen_edges[edge_idx] = pos_name
            edge_perm.append(edge_idx)

            # Orientação da aresta: 0 se actual_faces[0] == target_pair[0], senão 1
            ori = 0 if actual_faces[0] == target_pair[0] else 1
            edge_orient_sum += ori

        if errors:
            return ValidationResult(False, errors, warnings, color_counts)

        # 6. Verificar soma das orientações dos cantos (Corner Twist)
        if corner_orient_sum % 3 != 0:
            errors.append(
                "Estado fisicamente impossível (Canto Torcido / Corner Twist): "
                "pelo menos um canto está girado individualmente. Verifique as cores "
                "dos cantos ou a orientação das fotos."
            )

        # 7. Verificar soma das orientações das arestas (Edge Flip)
        if edge_orient_sum % 2 != 0:
            errors.append(
                "Estado fisicamente impossível (Aresta Invertida / Edge Flip): "
                "um número ímpar de arestas está invertido. Verifique as cores "
                "das arestas ou a orientação das fotos."
            )

        # 8. Verificar paridade global de permutação (Cantos vs Arestas)
        if len(corner_perm) == 8 and len(edge_perm) == 12:
            c_parity = _permutation_parity(corner_perm)
            e_parity = _permutation_parity(edge_perm)
            if c_parity != e_parity:
                errors.append(
                    "Estado fisicamente impossível (Erro de Paridade de Permutação): "
                    "duas peças foram trocadas isoladamente. Verifique se algum adesivo "
                    "foi classificado incorretamente ou se alguma foto está rotacionada."
                )

        return ValidationResult(len(errors) == 0, errors, warnings, color_counts)
