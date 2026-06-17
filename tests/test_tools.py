# tests/test_tools.py
# Run with: pytest tests/
# Note: suggest_outfit and create_fit_card tests require GROQ_API_KEY in .env

import pytest
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# --- search_listings ---
# these don't need an API key

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    # no listings should match a designer ballgown under $5
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)

def test_search_max_3_results():
    results = search_listings("shirt", size=None, max_price=None)
    assert len(results) <= 3

def test_search_result_has_required_fields():
    results = search_listings("tee", size=None, max_price=None)
    if results:
        for field in ["id", "title", "price", "platform", "condition", "style_tags"]:
            assert field in results[0]

def test_search_size_filter():
    results = search_listings("jeans", size="W30 L30", max_price=None)
    assert all("w30" in item["size"].lower() for item in results)


# --- suggest_outfit ---
# requires GROQ_API_KEY

def test_suggest_outfit_returns_string():
    results = search_listings("vintage tee", size=None, max_price=50)
    if not results:
        pytest.skip("no listings found for test item")
    suggestion = suggest_outfit(results[0], get_example_wardrobe())
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0

def test_suggest_outfit_empty_wardrobe():
    # should not crash — returns general styling advice instead
    results = search_listings("vintage tee", size=None, max_price=50)
    if not results:
        pytest.skip("no listings found for test item")
    suggestion = suggest_outfit(results[0], get_empty_wardrobe())
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0


# --- create_fit_card ---

def test_create_fit_card_empty_outfit():
    # empty outfit string should return an error message, not crash
    results = search_listings("tee", size=None, max_price=50)
    if not results:
        pytest.skip("no listings found for test item")
    result = create_fit_card("", results[0])
    assert isinstance(result, str)
    assert "error" in result.lower()

def test_create_fit_card_has_all_sections():
    # requires GROQ_API_KEY
    results = search_listings("vintage tee", size=None, max_price=50)
    if not results:
        pytest.skip("no listings found for test item")
    outfit = suggest_outfit(results[0], get_example_wardrobe())
    card = create_fit_card(outfit, results[0])
    assert "Item:" in card
    assert "Condition:" in card
    assert "Styling Tip:" in card
    assert "Caption:" in card
