"""The interface both agent implementations satisfy.

CLAUDE.md names this the one deliberate exception to "no abstraction before the
second case". It has exactly two implementations, `agents/custom.py` and
`agents/framework.py`, and it exists so that a signature drift between them
becomes a type error rather than a quiet divergence in the benchmark. Two agents
that no longer accept the same input are not being compared on architecture.

Nothing inherits from it. `Protocol` is structural, so both `call_agent`
functions satisfy it by shape alone. `framework.py` annotates itself against it
at module level, and `tests/test_framework_agent.py` checks the custom agent the
same way, which is what actually catches a drift.
"""

from collections.abc import Iterator, Sequence
from typing import Protocol

from agents.conversation import ConversationTurn
from agents.events import TraceEvent


class Agent(Protocol):
    """One run, from prompt to final answer, as a stream of trace events.

    `history` is the completed turns of the conversation so far. `generation` is
    the app-level selection, passed in rather than inferred, since type charts
    and a Pokemon's own typing depend on it.
    """

    def __call__(
        self,
        user_message: str,
        generation: int,
        history: Sequence[ConversationTurn] = (),
    ) -> Iterator[TraceEvent]: ...
