"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    # apply price and size filters
    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]
    if size is not None:
        # substring match so "M" catches "S/M", case-insensitive
        listings = [l for l in listings if size.lower() in l["size"].lower()]

    # score by keyword overlap across title, description, and style_tags
    keywords = description.lower().split()

    def score(listing):
        searchable = " ".join([
            listing["title"],
            listing["description"],
            " ".join(listing["style_tags"]),
        ]).lower()
        return sum(1 for kw in keywords if kw in searchable)

    scored = [(score(l), l) for l in listings]
    scored = [(s, l) for s, l in scored if s > 0]  # drop zero-overlap listings
    scored.sort(key=lambda x: x[0], reverse=True)

    return [l for _, l in scored[:3]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()
    items = wardrobe.get("items", [])

    if not items:
        # empty wardrobe — ask for general standalone styling advice
        prompt = (
            f"The user found this thrifted item: {new_item.get('title', 'item')} "
            f"(style: {', '.join(new_item.get('style_tags', []))}, "
            f"colors: {', '.join(new_item.get('colors', []))}).\n"
            "They don't have a saved wardrobe yet. "
            "Give 2-3 sentences of general styling advice for this item."
        )
    else:
        wardrobe_lines = "\n".join(
            f"- {item['name']} ({item['category']}, {', '.join(item.get('colors', []))})"
            for item in items
        )
        prompt = (
            f"The user found this thrifted item: {new_item.get('title', 'item')} "
            f"(style: {', '.join(new_item.get('style_tags', []))}, "
            f"colors: {', '.join(new_item.get('colors', []))}).\n\n"
            f"Their wardrobe:\n{wardrobe_lines}\n\n"
            "Suggest a specific outfit using the new item and named pieces from their wardrobe. "
            "Keep it to 2-3 sentences."
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        return (response.choices[0].message.content or "").strip()
    except Exception:
        return "Couldn't generate a suggestion — try pairing it with neutral basics."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # guard: empty or whitespace-only outfit string
    if not outfit or not outfit.strip():
        return "Error: outfit data is incomplete — no fit card generated."

    client = _get_groq_client()

    # use .get() with "N/A" fallbacks so missing keys don't crash
    title = new_item.get("title", "N/A")
    price = new_item.get("price", "N/A")
    platform = new_item.get("platform", "N/A")
    condition = new_item.get("condition", "N/A")
    style_tags = new_item.get("style_tags", [])

    prompt = (
        f"Write a short, casual social media caption (1-2 sentences) for this thrifted outfit post.\n"
        f"Item: {title} from {platform}, ${price}\n"
        f"Style: {', '.join(style_tags)}\n"
        f"Outfit: {outfit}\n"
        "Keep it authentic and fun. Include 2-3 relevant hashtags."
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.2,  # higher temp so captions vary each run
        )
        caption = (response.choices[0].message.content or "").strip()
    except Exception:
        caption = "N/A"

    return (
        f"Item: {title} | ${price} | {platform}\n"
        f"Condition: {condition}\n"
        f"Styling Tip: {outfit}\n"
        f"Caption: {caption}"
    )
