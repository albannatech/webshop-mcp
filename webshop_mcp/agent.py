"""The agent this extension brings, and the prompts it brings with it.

An extension is not only tools.  Every repo in this portfolio carries its own
tools, permissions, configurations, *agent* and *prompts* — and the agent is
what makes a set of tools into something with a point of view.

This module is pure data.  It is Frappe-free so it can be tested without a
site, and so the core can assemble a system prompt from it without importing
anything this extension depends on.

How the core uses it
--------------------
The core's prompt assembler is deterministic and ordered: the core's own system
prompt, then the *active* extension's agent persona, then its task prompts,
then the conversation.  One active agent per conversation, chosen in Settings
and switchable mid-thread with the switch recorded.  Twenty extensions
contribute *content*; none of them contributes assembly logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: This extension's name, as the core knows it.  It is the app name, because
#: that is what provenance is tagged with and what an uninstall keys on.
EXTENSION_NAME = "webshop_mcp"


@dataclass(frozen=True)
class Prompt:
    """One instruction the agent is given."""

    name: str
    text: str
    when: str = ""


@dataclass(frozen=True)
class Agent:
    """What this extension contributes to a conversation's point of view."""

    name: str
    persona: str
    boundaries: tuple[str, ...] = ()
    prompts: tuple[Prompt, ...] = field(default_factory=tuple)

    def always_on(self) -> tuple[Prompt, ...]:
        return tuple(p for p in self.prompts if not p.when)

    def for_situation(self, situation: str) -> tuple[Prompt, ...]:
        return tuple(p for p in self.prompts if p.when == situation)


AGENT = Agent(
    name="webshop_mcp",
    persona="You work with this site's catalogue and orders. You are careful about money and stock, because a price that is wrong by a factor of ten looks exactly like one that is right. You ask which currency and which warehouse before you report a figure.",
    boundaries=(
    "Never report a sales total without saying which currency and which period it covers.",
    "Never change a submitted document. It has to be cancelled and amended, which these tools do not do.",
    "Never invent a value to fill a required field. Ask for it.",
    "Never act on a record the user did not name.",
    ),
    prompts=(
        Prompt(
            name="working",
            text=(
                "Read the record before you change it, and show the reader "
                "what you are about to write. A change the reader did not see "
                "is a change they cannot catch."
            ),
            when="writing",
        ),
    ),
)


def system_prompt(situation: str = "") -> str:
    """The system prompt for this agent, deterministically assembled."""
    parts = [AGENT.persona]

    if AGENT.boundaries:
        parts.append("You will not:")
        parts.extend(f"- {b}" for b in AGENT.boundaries)

    for prompt in AGENT.always_on():
        parts.append(prompt.text)

    if situation:
        for prompt in AGENT.for_situation(situation):
            parts.append(prompt.text)

    return "\n\n".join(parts)
