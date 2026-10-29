"""Testes automatizados para validação física e lógica de estados do cubo."""

from cube_solver.models.cube_state import CubeState
from cube_solver.validation.validator import CubeValidator


def test_valid_solved_cube() -> None:
    """Cubo resolvido deve ser válido."""
    cube = CubeState.solved()
    res = CubeValidator.validate(cube)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_valid_scrambled_cube() -> None:
    """Qualquer cubo gerado por movimentos válidos deve passar na validação."""
    cube = CubeState.solved()
    cube.apply_sequence("R U2 F' D B2 L' U R' F D' L2 B")
    res = CubeValidator.validate(cube)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_invalid_color_count() -> None:
    """Alterar um único adesivo deve acusar contagem incorreta de cores."""
    cube = CubeState.solved()
    cube.set_sticker("U", 0, 0, "R")
    res = CubeValidator.validate(cube)
    assert res.is_valid is False
    assert any("Quantidade incorreta" in err for err in res.errors)


def test_invalid_duplicate_centers() -> None:
    """Dois centros da mesma cor (mesmo mantendo 9 adesivos de cada cor) devem falhar."""
    cube = CubeState.solved()
    # Troca centro de U ('W') com uma borda de F ('R')
    cube.set_sticker("U", 1, 1, "R")
    cube.set_sticker("F", 0, 1, "W")
    res = CubeValidator.validate(cube)
    assert res.is_valid is False
    assert any("Centro duplicado" in err for err in res.errors)


def test_invalid_corner_twist() -> None:
    """Girar um único canto (Corner Twist) deve ser detectado como estado impossível."""
    cube = CubeState.solved()
    # Canto URF: U[2,2], R[0,0], F[0,2] -> gira ciclicamente no sentido horário
    u_col = cube.faces["U"][2][2]
    r_col = cube.faces["R"][0][0]
    f_col = cube.faces["F"][0][2]
    cube.set_sticker("U", 2, 2, f_col)
    cube.set_sticker("R", 0, 0, u_col)
    cube.set_sticker("F", 0, 2, r_col)

    res = CubeValidator.validate(cube)
    assert res.is_valid is False
    assert any("Canto Torcido" in err for err in res.errors)


def test_invalid_edge_flip() -> None:
    """Inverter uma única aresta (Edge Flip) deve ser detectado como estado impossível."""
    cube = CubeState.solved()
    # Aresta UF: U[2,1] e F[0,1]
    u_col = cube.faces["U"][2][1]
    f_col = cube.faces["F"][0, 1] if isinstance(cube.faces["F"], tuple) else cube.faces["F"][0][1]
    cube.set_sticker("U", 2, 1, f_col)
    cube.set_sticker("F", 0, 1, u_col)

    res = CubeValidator.validate(cube)
    assert res.is_valid is False
    assert any("Aresta Invertida" in err for err in res.errors)


def test_invalid_permutation_parity() -> None:
    """Trocar duas arestas isoladamente deve falhar por erro de paridade de permutação."""
    cube = CubeState.solved()
    # Troca aresta UF (U[2,1], F[0,1]) com aresta UB (U[0,1], B[0,1])
    uf_u, uf_f = cube.faces["U"][2][1], cube.faces["F"][0][1]
    ub_u, ub_b = cube.faces["U"][0][1], cube.faces["B"][0][1]

    cube.set_sticker("U", 2, 1, ub_u)
    cube.set_sticker("F", 0, 1, ub_b)
    cube.set_sticker("U", 0, 1, uf_u)
    cube.set_sticker("B", 0, 1, uf_f)

    res = CubeValidator.validate(cube)
    assert res.is_valid is False
    assert any("Paridade de Permutação" in err for err in res.errors)
