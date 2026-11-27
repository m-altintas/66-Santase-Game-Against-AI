"""End-of-deal scoring (rules R5.3, R5.4, R7.1, R8.1, R8.1a, R8.2, R8.3)."""

from __future__ import annotations

from dataclasses import replace

from santase.engine.state import WIN_THRESHOLD, DealOutcome, DealState, EndReason, other

LAST_TRICK_BONUS = 10
SCHWARZ_LIMIT = 33  # opponent below this: 2 game points (R8.1)


def win_points(state: DealState, loser: int) -> int:
    """Game points for a regular win, judged on the loser (R8.1)."""
    if state.tricks_won[loser] == 0:
        return 3
    if state.card_points(loser) < SCHWARZ_LIMIT:
        return 2
    return 1


def penalty_points(state: DealState, receiver: int) -> int:
    """Game points the opponent of a failed closer or wrong declarer gets (R5.4, R8.1a)."""
    return 3 if state.tricks_won[receiver] == 0 else 2


def _finish(state: DealState, winner: int | None, points: int, reason: EndReason) -> DealState:
    totals = (state.card_points(0), state.card_points(1))
    return replace(state, outcome=DealOutcome(winner, points, reason, totals))


def score_declaration(state: DealState, declarer: int) -> DealState:
    """Resolve "out" (R8.1, R8.1a, R5.3, R5.4 via R8.3)."""
    opponent = other(declarer)
    correct = state.card_points(declarer) >= WIN_THRESHOLD
    closer = state.closed_by
    if closer is None or closer == declarer:
        if correct:
            reason = EndReason.CLOSER_WON if closer is not None else EndReason.DECLARED_OUT
            return _finish(state, declarer, win_points(state, opponent), reason)
        reason = EndReason.CLOSER_FAILED if closer is not None else EndReason.WRONG_DECLARATION
        return _finish(state, opponent, penalty_points(state, opponent), reason)
    # The closer's opponent declared.
    if correct:  # the opponent reached 66 first: the closer failed (R5.4)
        return _finish(state, declarer, penalty_points(state, declarer), EndReason.CLOSER_FAILED)
    return _finish(state, closer, penalty_points(state, closer), EndReason.WRONG_DECLARATION)


def score_exhausted(state: DealState) -> DealState:
    """All hands played out and nobody declared (R7.1, R8.2, R8.3)."""
    closer = state.closed_by
    if closer is not None:
        opponent = other(closer)
        if state.card_points(closer) >= WIN_THRESHOLD:
            return _finish(state, closer, win_points(state, opponent), EndReason.CLOSER_WON)
        return _finish(state, opponent, penalty_points(state, opponent), EndReason.CLOSER_FAILED)

    last = state.last_trick_winner
    assert last is not None
    bonus = [0, 0]
    bonus[last] = LAST_TRICK_BONUS
    state = replace(
        state, trick_points=(state.trick_points[0] + bonus[0], state.trick_points[1] + bonus[1])
    )
    first, second = state.card_points(0), state.card_points(1)
    if first == second:
        return _finish(state, None, 0, EndReason.DRAW)
    winner = 0 if first > second else 1
    return _finish(state, winner, win_points(state, other(winner)), EndReason.CARDS_EXHAUSTED)
