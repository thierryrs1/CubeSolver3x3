"""Testes unitários para o modelo CubeState e mecânica de movimentos."""

import pytest

from cube_solver.models.cube_state import CubeState


def test_solved_cube_initial_state() -> None:
    """Um cubo recém-criado deve estar resolvido."""
    cube = CubeState.solved()
    assert cube.is_solved() is True


@pytest.mark.parametrize("move", ["U", "D", "F", "B", "R", "L"])
def test_single_move_order_4(move: str) -> None:
    """Qualquer movimento de 90° aplicado 4 vezes deve retornar ao estado resolvido."""
    cube = CubeState.solved()
    cube.apply_move(move)
    assert cube.is_solved() is False
    for _ in range(3):
        cube.apply_move(move)
    assert cube.is_solved() is True


@pytest.mark.parametrize("move", ["U", "D", "F", "B", "R", "L"])
def test_move_and_inverse(move: str) -> None:
    """Um movimento seguido de seu inverso deve restaurar o cubo."""
    cube = CubeState.solved()
    cube.apply_move(move)
    cube.apply_move(f"{move}'")
    assert cube.is_solved() is True


@pytest.mark.parametrize("move", ["U2", "D2", "F2", "B2", "R2", "L2"])
def test_double_move_order_2(move: str) -> None:
    """Um movimento de 180° aplicado 2 vezes deve restaurar o cubo."""
    cube = CubeState.solved()
    cube.apply_move(move)
    assert cube.is_solved() is False
    cube.apply_move(move)
    assert cube.is_solved() is True


def test_sexy_move_order_6() -> None:
    """A sequência (R U R' U') repetida 6 vezes deve voltar ao estado inicial."""
    cube = CubeState.solved()
    for _ in range(6):
        cube.apply_sequence("R U R' U'")
    assert cube.is_solved() is True


def test_rotate_face_orientation() -> None:
    """Testa a rotação manual da orientação de uma única face em 90 graus."""
    cube = CubeState.solved()
    cube.set_face(
        "F",
        [
            ["W", "R", "G"],
            ["Y", "R", "O"],
            ["B", "W", "Y"],
        ],
    )
    original = cube.get_face("F")
    cube.rotate_face_orientation("F", clockwise=True)
    assert cube.get_face("F") != original
    cube.rotate_face_orientation("F", clockwise=False)
    assert cube.get_face("F") == original
