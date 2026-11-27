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
