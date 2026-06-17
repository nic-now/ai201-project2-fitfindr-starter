# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool takes the user's preferences/description of an item (such as size, price, and overall description) and then searches for matching listings. It picks the top 3 most relevant listings and returns them as a list. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- description (str): keywords for what the user wants, e.g. "vintage graphic tee"
- size (str): size to filter by like "S" or "M", None to skip
- max_price (float): max price in dollars, None to skip

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of up to 3 listing dicts ranked by relevance. Each one has: id, title, description, category, style_tags, size, condition, price, colors, brand, and platform. Returns an empty list if nothing matches.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
The agent saves an error message like "No listings found, try a different description or price" and stops without calling the other tools.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Takes the chosen listing and the users wardrobe and asks the LLM to suggest an outfit using both. Returns a short styling suggestion.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- new_item (dict): the selected listing from search_listings, needs title, style_tags, colors, and category
- wardrobe (dict): the users wardrobe dict with an items list, each item has name, category, colors, style_tags

**What it returns:**
<!-- Describe the return value -->
A short outfit suggestion, e.g. "Pair this tee with your baggy jeans and chunky sneakers for a Y2K look."

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty, still call the tool but tell the LLM to give general styling advice for the item on its own. If the LLM fails, return a fallback like "Try pairing it with neutral basics."

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Takes the outfit suggestion and the chosen item and formats them into a fit card with a social media caption.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- outfit (str): the suggestion string returned by suggest_outfit
- new_item (dict): the listing dict, needs title, price, platform, condition, and style_tags

**What it returns:**
<!-- Describe the return value -->
A formatted string with four labeled sections: Item (title, price, platform), Condition, Styling Tip (the outfit string), and Caption (a social media caption from the LLM).

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If outfit is empty or new_item is missing fields, fill in what you can and put n/a for anything missing. Always return something.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The agent runs tools in order and stops early if something fails:

1. Parse the query to get description, size, and max_price.
2. Call search_listings. If no results, save an error and stop early.
3. Take results[0] as selected_item. Call suggest_outfit. Use a fallback string if it returns empty.
4. Call create_fit_card with the outfit and selected item. Save the result.
5. Return the session. Done when fit_card is set.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent keeps a session dict through the whole interaction:

- query: the original user message
- description, size, max_price: parsed from the query
- all_results: up to 3 listings from search_listings
- selected_item: results[0], used in the next two tools
- outfit_suggestion: string from suggest_outfit, passed to create_fit_card
- fit_card: the final output string
- error: set if something fails, causes early return

Each tool gets its inputs as arguments. The loop pulls values from the session and passes them in.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Save an error message "No listings found, try a different search." Return early and skip the other tools. |
| suggest_outfit | Wardrobe is empty | Pass the empty wardrobe to the LLM anyway with a note. LLM returns general styling advice for the item alone. |
| create_fit_card | Outfit or item is incomplete | Fill in what you can and use "N/A" for missing fields. Still return the card. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```
User query
    │
    ▼
Planning Loop ─────────────────────────────────────────────────────┐
    │                                                              │
    ├─► [1] Parse query with LLM                                   │
    │       → session: description, size, max_price                │
    │                                                              │
    ├─► [2] search_listings(description, size, max_price)          │
    │           │                                                  │
    │           ├── results = [] ──► session["error"] set          │
    │           │                       │                          │
    │           │                       ▼                          │
    │           │                   [ERROR RETURN] ────────────────┘
    │           │
    │           └── results = [item, ...]
    │                   │
    │                   ▼
    │           session["selected_item"] = results[0]
    │           session["all_results"]   = results
    │                   │
    ├─► [3] suggest_outfit(selected_item, wardrobe)
    │           │
    │           ├── wardrobe empty → LLM gives standalone styling tip
    │           │
    │           └── outfit_suggestion = "Pair this with..."
    │                   │
    │                   ▼
    │           session["outfit_suggestion"] = outfit_suggestion
    │                   │
    └─► [4] create_fit_card(outfit_suggestion, selected_item)
                │
                ├── missing fields → fill with "N/A", still return card
                │
                └── fit_card = "Item: ...\nCondition: ...\nStyling Tip: ...\nCaption: ..."
                        │
                        ▼
                session["fit_card"] = fit_card
                        │
                        ▼
                  Return session → app.py displays fit_card to user
```

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

- search_listings: Give Claude Tool 1 section and the load_listings function signature. Ask it to implement search_listings in tools.py, filtering by size and price first then ranking by description with an LLM call. Check it returns an empty list on no match and that each result has all the right fields. Test with 3 different queries.

- suggest_outfit: Give Claude the Tool 2 section and the wardrobe_schema example. Ask it to implement suggest_outfit using a groqLLM call with the item and wardrobe as context. Check it handles an empty wardrobe and always returns a non-empty string.

- create_fit_card: Give Claude the Tool 3 section. Ask it to implement create_fit_card with string formatting for the four fields and an LLM call for the caption. Check all four fields show up and missing keys use n/a.

**Milestone 4 — Planning loop and state management:**

Give Claude the architecture diagram and the planning loop and state sections. Ask it to implement run_agent in agent.py. Check that fit_card is set for a normal query and that a no-match query sets error and skips the other tools.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
Agent uses search_listing() tool to look for items matching description, size, and price. The tool returns 3 matching listings sorted by relevance. Agent chooses the top choice.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
Agent uses suggest_outfit() tool to find possible outfits between new item and items in the current wardrobe. It returns a short outfit suggestion.

**Step 3:**
<!-- Continue until the full interaction is complete -->
Agent uses create_fit_card() tool to create a look card using the outfit suggestion and item details. It generates a social media caption and formats everything into a readable card.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees a fit card showing the item name, price, condition, a styling tip, and a caption they can copy for a social media post.
