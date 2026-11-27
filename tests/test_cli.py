"""Smoke test: the terminal game runs a whole match on scripted input."""

import pytest

from santase import cli


def test_cli_plays_a_match_to_the_end(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = iter(["x", "99", *["1"] * 500])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    match = cli.play(seed=7, target=3)
    assert match.is_over
    out = capsys.readouterr().out
    assert "Pick a number" in out
    assert "Deal over" in out


def test_every_action_and_event_has_text() -> None:
    from helpers import c

    from santase.engine import Announce, Close, Declare, Exchange, Play, Suit
    from santase.engine.state import (
        CardPlayed,
        MarriageAnnounced,
        OutDeclared,
        TalonClosed,
        TrickTaken,
        TrumpCardTaken,
        TrumpExchanged,
        TrumpTurned,
    )

    for action in (Play(c("AH")), Announce(Suit.HEARTS), Exchange(), Close(), Declare()):
        assert cli.describe(action)
    events = (
        CardPlayed(0, c("AH")),
        TrickTaken(1),
        MarriageAnnounced(0, Suit.HEARTS, 20),
        TrumpExchanged(1, c("9S"), c("AS")),
        TalonClosed(0),
        TrumpCardTaken(1, c("AS")),
        OutDeclared(0),
    )
    for event in events:
        assert cli.narrate(event)
    assert cli.narrate(TrumpTurned(c("AS"))) is None


def test_main_parses_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr("sys.argv", ["santase", "--seed", "4", "--target", "2"])
    monkeypatch.setattr(cli, "play", lambda seed, target: calls.append((seed, target)))
    cli.main()
    assert calls == [(4, 2)]
