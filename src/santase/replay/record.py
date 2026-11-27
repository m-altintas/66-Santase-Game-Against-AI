"""Match records and the validator that replays them through the engine."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from santase.engine import (
    RULES_VERSION,
    Action,
    IllegalActionError,
    MatchState,
    match_step,
    new_match,
    parse_action,
)

MAX_TARGET = 1_000
MAX_ACTIONS = 100_000
MAX_SEED_LENGTH = 256


class ReplayError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MatchRecord:
    seed: int | str
    target: int
    actions: tuple[str, ...]
    rules_version: int = RULES_VERSION

    def to_json(self) -> str:
        return json.dumps(
            {
                "rules_version": self.rules_version,
                "seed": self.seed,
                "target": self.target,
                "actions": list(self.actions),
            }
        )

    @staticmethod
    def from_json(text: str) -> MatchRecord:
        """Parse an untrusted record; any malformed input raises ReplayError."""
        try:
            data: Any = json.loads(text)
        except (ValueError, RecursionError) as exc:  # JSONDecodeError is a ValueError
            raise ReplayError(f"malformed record: {exc}") from exc
        if not isinstance(data, dict):
            raise ReplayError("a record must be a JSON object")
        record: dict[str, Any] = data  # pyright: ignore[reportUnknownVariableType]
        try:
            seed, target = record["seed"], record["target"]
            actions, version = record["actions"], record["rules_version"]
        except KeyError as exc:
            raise ReplayError(f"missing field {exc}") from exc
        if not _is_int(version):
            raise ReplayError("rules_version must be an int")
        if not (_is_int(target) and 1 <= target <= MAX_TARGET):
            raise ReplayError(f"target must be an int from 1 to {MAX_TARGET}")
        if not _valid_seed(seed):
            raise ReplayError("seed must be an int or a UTF-8 string")
        if not isinstance(actions, list) or len(actions) > MAX_ACTIONS:  # pyright: ignore[reportUnknownArgumentType]
            raise ReplayError(f"actions must be a list of at most {MAX_ACTIONS} strings")
        texts: list[Any] = actions  # pyright: ignore[reportUnknownVariableType]
        if not all(isinstance(a, str) for a in texts):
            raise ReplayError("actions must be strings")
        return MatchRecord(seed, target, tuple(texts), version)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_seed(seed: object) -> bool:
    if _is_int(seed):
        return True
    if not isinstance(seed, str) or len(seed) > MAX_SEED_LENGTH:
        return False
    try:
        seed.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def record_actions(seed: int | str, target: int, actions: list[Action]) -> MatchRecord:
    return MatchRecord(seed, target, tuple(str(a) for a in actions))


def replay(record: MatchRecord) -> MatchState:
    """Replay a record; raise ReplayError on any illegal or unparsable action."""
    if record.rules_version != RULES_VERSION:
        raise ReplayError(f"unsupported rules version {record.rules_version}")
    match = new_match(record.seed, record.target)
    for index, text in enumerate(record.actions):
        try:
            match = match_step(match, parse_action(text))
        except (IllegalActionError, ValueError) as exc:
            raise ReplayError(f"action {index} ({text!r}): {exc}") from exc
    return match
