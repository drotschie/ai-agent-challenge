"""Conversational pronoun resolution, entity extraction, and query decomposition.

Performs deterministic regex and dictionary entity recognition over South African suburbs,
crops, and soil pH values, with fallback LLM query reformulation. Resolves conversational
pronouns from chat history.
"""

import csv
from functools import lru_cache
import json
import re
from typing import Any

from app.config import generate_json_with_llm, get_settings
from app.rag.schemas import ChatMessage, QueryTransformResult, SubQuery

# Canonical crop aliases and common plural forms
CROP_ALIASES: dict[str, str] = {
    "tomato": "Heirloom Tomato",
    "tomatoes": "Heirloom Tomato",
    "heirloom tomato": "Heirloom Tomato",
    "heirloom tomatoes": "Heirloom Tomato",
    "spinach": "Spinach",
    "pepper": "Sweet Pepper",
    "peppers": "Sweet Pepper",
    "sweet pepper": "Sweet Pepper",
    "sweet peppers": "Sweet Pepper",
    "bell pepper": "Sweet Pepper",
    "bell peppers": "Sweet Pepper",
    "bean": "Green Beans",
    "beans": "Green Beans",
    "green bean": "Green Beans",
    "green beans": "Green Beans",
    "broad bean": "Broad Bean",
    "broad beans": "Broad Bean",
    "pea": "Garden Peas",
    "peas": "Garden Peas",
    "garden pea": "Garden Peas",
    "garden peas": "Garden Peas",
    "carrot": "Carrot",
    "carrots": "Carrot",
    "blueberry": "Blueberry",
    "blueberries": "Blueberry",
    "potato": "Potato",
    "potatoes": "Potato",
    "sweet potato": "Sweet Potato",
    "sweet potatoes": "Sweet Potato",
    "strawberry": "Strawberry",
    "strawberries": "Strawberry",
    "onion": "Red Onion",
    "onions": "Red Onion",
    "red onion": "Red Onion",
    "red onions": "Red Onion",
    "chilli": "Chilli Pepper",
    "chillies": "Chilli Pepper",
    "chili": "Chilli Pepper",
    "chilies": "Chilli Pepper",
    "chilli pepper": "Chilli Pepper",
    "chilli peppers": "Chilli Pepper",
    "pumpkin": "Pumpkin",
    "pumpkins": "Pumpkin",
    "squash": "Butternut Squash",
    "butternut": "Butternut Squash",
    "butternut squash": "Butternut Squash",
    "cabbage": "Cabbage",
    "cabbages": "Cabbage",
    "radish": "Radish",
    "radishes": "Radish",
    "turnip": "Turnip",
    "turnips": "Turnip",
    "eggplant": "Eggplant",
    "eggplants": "Eggplant",
    "aubergine": "Eggplant",
    "aubergines": "Eggplant",
    "cucumber": "Cucumber",
    "cucumbers": "Cucumber",
    "watermelon": "Watermelon",
    "watermelons": "Watermelon",
    "zucchini": "Zucchini",
    "zucchinis": "Zucchini",
    "courgette": "Zucchini",
    "courgettes": "Zucchini",
    "beetroot": "Beetroot",
    "beetroots": "Beetroot",
    "beet": "Beetroot",
    "beets": "Beetroot",
    "leek": "Leek",
    "leeks": "Leek",
    "artichoke": "Artichoke",
    "artichokes": "Artichoke",
    "kale": "Kale",
    "lettuce": "Lettuce",
    "cauliflower": "Cauliflower",
    "broccoli": "Broccoli",
    "sweet corn": "Sweet Corn",
    "corn": "Sweet Corn",
    "swiss chard": "Swiss Chard",
    "chard": "Swiss Chard",
    "cape gooseberry": "Cape Gooseberry",
    "gooseberry": "Cape Gooseberry",
    "gooseberries": "Cape Gooseberry",
    "garlic": "Garlic",
    "basil": "Basil",
    "rosemary": "Rosemary",
    "thyme": "Thyme",
    "mint": "Mint",
    "fennel": "Fennel",
    "coriander": "Coriander",
    "cilantro": "Coriander",
    "parsley": "Parsley",
}


@lru_cache(maxsize=1)
def get_known_suburbs() -> list[str]:
    """Load canonical suburb names from regional_soil_and_climate.csv.

    Prioritizes longer multi-word names first so compound suburbs match before substrings.
    """
    settings = get_settings()
    csv_path = settings.data_dir / "regional_soil_and_climate.csv"
    suburbs: list[str] = []
    if csv_path.exists():
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                suburb = row.get("suburb", "").strip()
                if suburb and suburb not in suburbs:
                    suburbs.append(suburb)

    # Sort descending by length to prioritize names like "Mitchells Plain" or "Somerset West"
    suburbs.sort(key=lambda s: len(s), reverse=True)
    return suburbs


@lru_cache(maxsize=1)
def get_known_crops() -> list[str]:
    """Load canonical crop names from crop_planting_guide.json."""
    settings = get_settings()
    json_path = settings.data_dir / "crop_planting_guide.json"
    crops: list[str] = []
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            guide = json.load(f)
            for entry in guide:
                crop = entry.get("crop_name", "").strip()
                if crop and crop not in crops:
                    crops.append(crop)

    crops.sort(key=lambda c: len(c), reverse=True)
    return crops


def detect_suburb(text: str) -> str | None:
    """Detect known suburb in text using boundary-aware regex matching."""
    known_suburbs = get_known_suburbs()
    for sub in known_suburbs:
        # Match with optional apostrophe for names like Mitchell's Plain / Simons Town
        escaped = re.escape(sub).replace(r"\'", r"\'?")
        pattern = rf"\b{escaped}\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            return sub
    return None


def detect_crops(text: str) -> list[str]:
    """Detect canonical crop names in text using direct names and alias dictionary."""
    found: list[str] = []

    # 1. Match against alias keys sorted by length descending
    sorted_aliases = sorted(CROP_ALIASES.keys(), key=lambda k: len(k), reverse=True)
    for alias in sorted_aliases:
        pattern = rf"\b{re.escape(alias)}\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            canonical = CROP_ALIASES[alias]
            if canonical not in found:
                found.append(canonical)

    # 2. Match against canonical crop names directly
    for crop in get_known_crops():
        pattern = rf"\b{re.escape(crop)}\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            if crop not in found:
                found.append(crop)

    return found


def detect_soil_ph(text: str) -> float | None:
    """Extract soil pH value from text using standard soil science patterns."""
    patterns = [
        re.compile(r"(?:ph|pH)\s*(?:of|is|=|:|at)?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
        re.compile(r"(\d+(?:\.\d+)?)\s*(?:ph|pH)", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            try:
                val = float(match.group(1))
                if 3.0 <= val <= 10.0:
                    return val
            except (ValueError, TypeError):
                continue
    return None


def _build_deterministic_transform(
    question: str,
    chat_history: list[ChatMessage] | None,
    suburb: str | None,
    crops: list[str],
    soil_ph: float | None,
    suburb_from_history: bool,
    crops_from_history: bool,
    ph_from_history: bool,
) -> dict[str, Any]:
    """Construct deterministic query transform result with pronoun resolution."""
    resolved = question

    # Conversational pronoun and spatial reference resolution
    if suburb and suburb_from_history:
        sub_pattern = re.compile(
            r"\b(there|that suburb|my area|in that town|in that area|in the area)\b",
            re.IGNORECASE,
        )
        if sub_pattern.search(resolved):
            resolved = sub_pattern.sub(f"in {suburb}", resolved)
        else:
            resolved = f"{resolved} (location: {suburb})"

    if crops and crops_from_history:
        crop_names_str = ", ".join(crops)
        crop_pattern = re.compile(
            r"\b(it|them|that crop|those crops)\b",
            re.IGNORECASE,
        )
        if crop_pattern.search(resolved):
            resolved = crop_pattern.sub(crop_names_str, resolved)
        else:
            resolved = f"{resolved} (crops: {crop_names_str})"

    if soil_ph is not None and ph_from_history:
        if not re.search(r"(?:ph|pH)", resolved, re.IGNORECASE):
            resolved = f"{resolved} (soil pH: {soil_ph})"

    crop_terms = ", ".join(crops) if crops else question
    sub_queries = [
        {
            "target_source": "regional_soil_and_climate.csv",
            "query": (
                f"{suburb or 'Cape Town Western Cape'} soil type baseline soil pH "
                "climate zone frost risk annual rainfall"
            ),
        },
        {
            "target_source": "crop_planting_guide.json",
            "query": (
                f"{crop_terms} optimal soil pH range temperature "
                "water needs planting months"
            ),
        },
        {
            "target_source": "soil_treatment_and_watering_rules.pdf",
            "query": (
                f"agricultural lime elemental sulfur dosage g/m2 soil pH "
                f"{soil_ph or ''} watering adjustment rules"
            ),
        },
    ]

    return {
        "resolved_question": resolved,
        "detected_suburb": suburb,
        "detected_crops": crops,
        "detected_soil_ph": soil_ph,
        "sub_queries": sub_queries,
    }


def transform_query(
    question: str,
    chat_history: list[ChatMessage] | None = None,
) -> QueryTransformResult:
    """Transform user question with conversational pronoun resolution and entity extraction.

    Scans question first, falling back to chat_history in reverse order.
    Generates targeted sub-queries for all 3 reference sources.
    """
    history = chat_history or []

    # 1. Suburb detection
    suburb = detect_suburb(question)
    suburb_from_history = False
    if not suburb and history:
        for msg in reversed(history):
            found_sub = detect_suburb(msg.content)
            if found_sub:
                suburb = found_sub
                suburb_from_history = True
                break

    # 2. Crop detection
    crops = detect_crops(question)
    crops_from_history = False
    if not crops and history:
        for msg in reversed(history):
            found_crops = detect_crops(msg.content)
            if found_crops:
                crops = found_crops
                crops_from_history = True
                break

    # 3. Soil pH detection
    soil_ph = detect_soil_ph(question)
    ph_from_history = False
    if soil_ph is None and history:
        for msg in reversed(history):
            found_ph = detect_soil_ph(msg.content)
            if found_ph is not None:
                soil_ph = found_ph
                ph_from_history = True
                break

    # 4. Build deterministic baseline
    fallback_data = _build_deterministic_transform(
        question=question,
        chat_history=history,
        suburb=suburb,
        crops=crops,
        soil_ph=soil_ph,
        suburb_from_history=suburb_from_history,
        crops_from_history=crops_from_history,
        ph_from_history=ph_from_history,
    )

    # 5. LLM query transformation with deterministic fallback
    system_prompt = (
        "You are an expert South African agronomy query parser. Analyze the user question "
        "and conversation history. Produce a JSON object with: resolved_question (string, "
        "resolving all pronouns), detected_suburb (string or null), detected_crops (array of "
        "strings), detected_soil_ph (float or null), and sub_queries (array of 3 objects "
        "with keys 'target_source' and 'query' covering 'regional_soil_and_climate.csv', "
        "'crop_planting_guide.json', and 'soil_treatment_and_watering_rules.pdf')."
    )

    history_text = "\n".join(f"{m.role}: {m.content}" for m in history)
    user_prompt = (
        f"Conversation History:\n{history_text or 'None'}\n\n"
        f"User Question:\n{question}\n\n"
        f"Deterministic Extraction Hints:\n"
        f"- Suburb: {suburb}\n"
        f"- Crops: {crops}\n"
        f"- Soil pH: {soil_ph}"
    )

    parsed, _ = generate_json_with_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        fallback_fn=lambda: fallback_data,
    )

    # 6. Validate and merge to guarantee deterministic entities and all 3 sources
    final_suburb = suburb or parsed.get("detected_suburb")
    final_crops = list(set(crops + [c for c in parsed.get("detected_crops", []) if isinstance(c, str)]))
    final_ph = soil_ph if soil_ph is not None else parsed.get("detected_soil_ph")
    try:
        final_ph = float(final_ph) if final_ph is not None else None
    except (ValueError, TypeError):
        final_ph = soil_ph

    resolved_q = parsed.get("resolved_question")
    if not resolved_q or not isinstance(resolved_q, str) or len(resolved_q.strip()) == 0:
        resolved_q = fallback_data["resolved_question"]

    # Ensure all 3 required sources are present in sub_queries
    sub_queries_raw = parsed.get("sub_queries")
    required_sources = {
        "regional_soil_and_climate.csv",
        "crop_planting_guide.json",
        "soil_treatment_and_watering_rules.pdf",
    }

    final_sub_queries: list[SubQuery] = []
    seen_sources: set[str] = set()

    if isinstance(sub_queries_raw, list):
        for sq in sub_queries_raw:
            if isinstance(sq, dict) and "target_source" in sq and "query" in sq:
                src = str(sq["target_source"]).strip()
                q_text = str(sq["query"]).strip()
                if src in required_sources and q_text:
                    final_sub_queries.append(SubQuery(target_source=src, query=q_text))
                    seen_sources.add(src)

    # Fill in any missing target sources from deterministic fallback
    for fb_sq in fallback_data["sub_queries"]:
        if fb_sq["target_source"] not in seen_sources:
            final_sub_queries.append(
                SubQuery(
                    target_source=fb_sq["target_source"],
                    query=fb_sq["query"],
                )
            )
            seen_sources.add(fb_sq["target_source"])

    return QueryTransformResult(
        resolved_question=resolved_q,
        detected_suburb=final_suburb,
        detected_crops=final_crops,
        detected_soil_ph=final_ph,
        sub_queries=final_sub_queries,
    )
