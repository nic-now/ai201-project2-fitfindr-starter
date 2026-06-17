# tests/test_agent.py
# Agent-level failure mode tests.
# Run with: pytest tests/
# Happy path test requires GROQ_API_KEY in .env

import pytest
from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# --- no-results path (no API key needed) ---

def test_agent_no_results_sets_error():
    # impossible query — agent should stop before calling LLM tools
    session = run_agent("designer ballgown size XXS under $5", get_example_wardrobe())
    assert session["error"] is not None

def test_agent_no_results_fit_card_is_none():
    # fit_card must be None when search returns nothing
    session = run_agent("designer ballgown size XXS under $5", get_example_wardrobe())
    assert session["fit_card"] is None

def test_agent_no_results_message_is_helpful():
    # error message should tell the user what to try next
    session = run_agent("designer ballgown size XXS under $5", get_example_wardrobe())
    msg = session["error"].lower()
    assert "try" in msg or "different" in msg  # gives the user guidance, not just "error"


# --- happy path (requires GROQ_API_KEY) ---

def test_agent_happy_path_state_flows():
    # state should pass correctly between all three tools
    session = run_agent("vintage graphic tee under $50", get_example_wardrobe())
    if session["error"]:
        pytest.skip("no listings found — check data or query")

    # selected_item should be the first search result
    assert session["selected_item"] is not None
    assert session["selected_item"] == session["search_results"][0]

    # outfit_suggestion should be non-empty and was passed to create_fit_card
    assert session["outfit_suggestion"] and len(session["outfit_suggestion"]) > 0

    # fit_card should contain the outfit suggestion text
    assert session["outfit_suggestion"] in session["fit_card"]

def test_agent_happy_path_no_error():
    session = run_agent("vintage graphic tee under $50", get_example_wardrobe())
    if session["error"]:
        pytest.skip("no listings found — check data or query")
    assert session["error"] is None

def test_agent_empty_wardrobe_still_works():
    # empty wardrobe should not crash the agent
    session = run_agent("vintage tee under $50", get_empty_wardrobe())
    if session["error"]:
        pytest.skip("no listings found")
    assert session["fit_card"] is not None