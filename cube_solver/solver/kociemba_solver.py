"""Resolução determinística do cubo mágico usando kociemba com verificação por simulação."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import kociemba

from cube_solver.models.cube_state import CubeState
from cube_solver.solver.notation import explain_move, state_to_kociemba
from cube_solver.validation.validator import CubeValidator, ValidationResult


@dataclass
class SolutionResult:
    """Resultado completo do cálculo da solução."""

    success: bool
    moves: List[str] = field(default_factory=list)
    kociemba_string: str = ""
    is_already_solved: bool = False
    error_message: str = ""
    validation: Optional[ValidationResult] = None

    @property
    def move_count(self) -> int:
        """Retorna o número total de movimentos da solução."""
        return len(self.moves)

    @property
    def notation_text(self) -> str:
        """Retorna a sequência de movimentos formatada em texto."""
        if self.is_already_solved:
            return "Cubo já está resolvido (0 movimentos)."
        return " ".join(self.moves)

    def get_step_descriptions(self) -> List[Tuple[int, str, str]]:
        """Retorna lista de (indice_1_based, notacao, explicacao_pt)."""
        return [
            (idx + 1, move, explain_move(move))
            for idx, move in enumerate(self.moves)
        ]


class CubeSolverEngine:
    """
    Motor determinístico de resolução que valida o estado, converte para a
    notação Kociemba, calcula a solução ótima/sub-ótima e simula os movimentos
    para garantir que o cubo termine 100% resolvido.
    """

    @staticmethod
    def solve(state: CubeState) -> SolutionResult:
        """
        Valida o estado do cubo, calcula a sequência de movimentos com kociemba
        e testa a sequência calculada antes de declará-la válida.
        """
        # 1. Validação física e combinatória completa
        validation = CubeValidator.validate(state)
        if not validation.is_valid:
            return SolutionResult(
                success=False,
                error_message=validation.summary,
                validation=validation,
            )

        # 2. Conversão para string Kociemba
        try:
            k_str = state_to_kociemba(state)
        except ValueError as exc:
            return SolutionResult(
                success=False,
                error_message=f"Erro na conversão para notação Kociemba: {exc}",
                validation=validation,
            )

        # 3. Verificar se já está resolvido
        if state.is_solved():
            return SolutionResult(
                success=True,
                moves=[],
                kociemba_string=k_str,
                is_already_solved=True,
                validation=validation,
            )

        # 4. Resolver via biblioteca kociemba (algoritmo determinístico Two-Phase)
        try:
            solution_str = kociemba.solve(k_str)
        except Exception as exc:
            return SolutionResult(
                success=False,
                kociemba_string=k_str,
                error_message=(
                    f"A biblioteca kociemba rejeitou a configuração informada: {exc}"
                ),
                validation=validation,
            )

        moves = [m.strip() for m in solution_str.strip().split() if m.strip()]

        # 5. Requisito 34: Testar a sequência calculada em uma cópia do estado
        # antes de declarar a solução válida.
        test_cube = state.copy()
        try:
            test_cube.apply_sequence(moves)
        except ValueError as exc:
            return SolutionResult(
                success=False,
                kociemba_string=k_str,
                error_message=f"Erro ao simular a sequência calculada: {exc}",
                validation=validation,
            )

        if not test_cube.is_solved():
            return SolutionResult(
                success=False,
                kociemba_string=k_str,
                error_message=(
                    "Falha na verificação pós-cálculo: a sequência gerada não "
                    "levou o cubo ao estado resolvido."
                ),
                validation=validation,
            )

        return SolutionResult(
            success=True,
            moves=moves,
            kociemba_string=k_str,
            is_already_solved=False,
            validation=validation,
        )
