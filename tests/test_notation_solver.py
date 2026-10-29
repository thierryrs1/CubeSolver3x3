"""Testes automatizados para conversão Kociemba e resolução do cubo."""

import pytest

from cube_solver.models.cube_state import CubeState
from cube_solver.solver.kociemba_solver import CubeSolverEngine
from cube_solver.solver.notation import (
    explain_move,
    kociemba_to_state,
    state_to_kociemba,
)


def test_solved_kociemba_notation() -> None:
    """O cubo resolvido deve gerar a string padrão de 54 caracteres."""
    cube = CubeState.solved()
    k_str = state_to_kociemba(cube)
    assert k_str == "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"

    restored = kociemba_to_state(k_str)
    assert restored.is_solved() is True
    assert state_to_kociemba(restored) == k_str


def test_solver_on_solved_cube() -> None:
    """Resolver um cubo já resolvido deve retornar sucesso com 0 movimentos."""
    cube = CubeState.solved()
    result = CubeSolverEngine.solve(cube)
    assert result.success is True
    assert result.is_already_solved is True
    assert result.moves == []


@pytest.mark.parametrize(
    "scramble",
    [
        "R U R' U'",
        "F R U R' U' F'",
        "U2 D2 F2 B2 L2 R2",
        "R U2 F' D B2 L' U R' F D' L2 B U' R2 F2",
        "L' U' B D2 R F' U2 B' L D' R' F2 U",
    ],
)
def test_solver_on_valid_scrambles(scramble: str) -> None:
    """Testa se o solver resolve diversos embaralhamentos válidos com sucesso."""
    cube = CubeState.solved()
    cube.apply_sequence(scramble)
    assert cube.is_solved() is False

    result = CubeSolverEngine.solve(cube)
    assert result.success is True
    assert result.is_already_solved is False
    assert len(result.moves) > 0

    # Aplica a solução e confirma que o cubo fica resolvido
    cube.apply_sequence(result.moves)
    assert cube.is_solved() is True


def test_solver_on_cubo_png_reference_state() -> None:
    """Testa o estado exato presente na imagem de referência cubo.png do projeto."""
    faces = {
        "U": [
            ["Y", "O", "Y"],
            ["O", "W", "B"],
            ["R", "G", "B"],
        ],
        "L": [
            ["G", "W", "Y"],
            ["R", "B", "Y"],
            ["O", "W", "G"],
        ],
        "F": [
            ["G", "Y", "O"],
            ["O", "R", "W"],
            ["R", "B", "O"],
        ],
        "R": [
            ["Y", "W", "R"],
            ["R", "G", "R"],
            ["G", "G", "R"],
        ],
        "B": [
            ["B", "G", "O"],
            ["Y", "O", "B"],
            ["B", "B", "B"],
        ],
        "D": [
            ["W", "Y", "W"],
            ["G", "Y", "R"],
            ["W", "O", "W"],
        ],
    }
    cube = CubeState(faces)
    result = CubeSolverEngine.solve(cube)
    assert result.success is True
    cube.apply_sequence(result.moves)
    assert cube.is_solved() is True


def test_solver_rejects_impossible_cube() -> None:
    """O motor de resolução deve recusar estados fisicamente impossíveis."""
    cube = CubeState.solved()
    # Inverte uma aresta
    u_col = cube.faces["U"][2][1]
    f_col = cube.faces["F"][0][1]
    cube.set_sticker("U", 2, 1, f_col)
    cube.set_sticker("F", 0, 1, u_col)

    result = CubeSolverEngine.solve(cube)
    assert result.success is False
    assert "Aresta Invertida" in result.error_message


def test_explain_move_pt() -> None:
    """Garante que todos os 18 movimentos possuem explicação clara em português."""
    for base in ["U", "D", "F", "B", "R", "L"]:
        for suffix in ["", "'", "2"]:
            move = f"{base}{suffix}"
            explanation = explain_move(move)
            assert "Gire a face" in explanation
