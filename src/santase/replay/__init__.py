"""Game records: a match is fully described by (rules version, seed, target, actions)."""

from santase.replay.record import MatchRecord, ReplayError, record_actions, replay

__all__ = ["MatchRecord", "ReplayError", "record_actions", "replay"]
