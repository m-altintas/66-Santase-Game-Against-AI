"""Exact solver for deals with no more draws (talon closed or exhausted).

Once nothing is left to draw, a fully known deal is a finite two-player perfect-information
game, so negamax with alpha-beta and a transposition table finds the exact game-point value.
Inside the real game this applies when the talon is exhausted (every unseen card is then in
the opponent's hand); the search bots also use it on determinized worlds.
"""

from __future__ import annotations

from santase.engine import Action, DealState, Declare, legal_actions, step

Key = tuple[object, ...]


def outcome_value(state: DealState, player: int) -> int:
    """Signed game points of a finished deal, from `player`'s side."""
    outcome = state.outcome
    assert outcome is not None
    if outcome.winner is None:
        return 0
    return outcome.game_points if outcome.winner == player else -outcome.game_points


def _key(state: DealState) -> Key:
    return (
        state.hands,
        state.turn,
        state.leader,
        state.trick,
        state.trick_points,
        state.marriage_points,
        state.tricks_won,
        state.announced,
        state.closed_by,
        state.last_trick_winner,
        len(state.talon),
    )


class EndgameSolver:
    """Negamax over game points. Use one instance per deal: the table assumes one trump suit."""

    def __init__(self) -> None:
        self._table: dict[Key, tuple[int, int]] = {}  # key -> (bound flag, value)
        self.nodes = 0

    def solve(self, state: DealState) -> tuple[int, Action]:
        """Best action and its value for the player to move."""
        if not state.strict or state.is_over:
            raise ValueError("the solver needs a live deal with no more draws")
        best_value, best_action = -99, None
        alpha = -99
        for action in _ordered(state):
            value = self._value(step(state, action), state.turn, alpha, 99)
            if value > best_value:
                best_value, best_action = value, action
                alpha = max(alpha, value)
        assert best_action is not None
        return best_value, best_action

    def values(self, state: DealState) -> dict[Action, int]:
        """Exact value of every legal action, for the player to move."""
        return {a: self._value(step(state, a), state.turn, -99, 99) for a in legal_actions(state)}

    def _value(self, state: DealState, player: int, alpha: int, beta: int) -> int:
        """Value of `state` for `player` (who just moved), within (alpha, beta)."""
        if state.is_over:
            return outcome_value(state, player)
        mover = state.turn
        if mover != player:
            return -self._negamax(state, -beta, -alpha)
        return self._negamax(state, alpha, beta)

    def _negamax(self, state: DealState, alpha: int, beta: int) -> int:
        """Value for the player to move."""
        self.nodes += 1
        key = _key(state)
        hit = self._table.get(key)
        if hit is not None:
            flag, value = hit
            if flag == 0 or (flag < 0 and value <= alpha) or (flag > 0 and value >= beta):
                return value
        original_alpha = alpha
        best = -99
        for action in _ordered(state):
            value = self._value(step(state, action), state.turn, alpha, beta)
            best = max(best, value)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        flag = -1 if best <= original_alpha else (1 if best >= beta else 0)
        self._table[key] = (flag, best)
        return best


def _ordered(state: DealState) -> list[Action]:
    actions = list(legal_actions(state))
    actions.sort(key=lambda a: not isinstance(a, Declare))  # try the declaration first
    return actions
