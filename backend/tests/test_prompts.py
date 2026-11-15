"""The shared system prompt is the same text for both agents."""

from agents import custom, framework
from agents.prompts import SYSTEM_PROMPT


def test_both_agents_share_one_system_prompt() -> None:
    assert custom.SYSTEM_PROMPT is SYSTEM_PROMPT
    assert framework.SYSTEM_PROMPT is SYSTEM_PROMPT


def test_pokemon_news_is_in_scope_and_uses_web_search() -> None:
    assert "Answer a Pokemon news question with web_search" in SYSTEM_PROMPT
    assert "Cite the sources web_search returned." in SYSTEM_PROMPT
    assert "Do not answer it from memory." in SYSTEM_PROMPT
    # The old scope sentence listed only battle topics, so the custom loop
    # refused Pokemon news as off-topic.
    assert (
        "You only discuss Pokemon: team building, matchups, stats, moves, "
        "typings, and battle strategy."
    ) not in SYSTEM_PROMPT


def test_no_selected_generation_defaults_to_the_latest_games() -> None:
    assert (
        "When no generation is selected and the question does not name one, "
        "answer for the latest games."
    ) in SYSTEM_PROMPT
    assert "Mention generation differences briefly when they matter." in SYSTEM_PROMPT
    # The previous instruction treated a generation as always selected.
    assert (
        "Use the selected generation as the default when the question leaves "
        "it unspecified."
    ) not in SYSTEM_PROMPT


def test_news_that_is_not_about_pokemon_is_declined_without_search() -> None:
    assert "News that is not linked to Pokemon is outside what you do." in SYSTEM_PROMPT
    assert "Decline it briefly and politely" in SYSTEM_PROMPT
    assert "Do not search for it" in SYSTEM_PROMPT
    assert "never search for news that is not about Pokemon." in SYSTEM_PROMPT
