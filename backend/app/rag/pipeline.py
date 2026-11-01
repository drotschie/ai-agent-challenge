"""End-to-end Part 1 Structured RAG pipeline and live Open-Meteo weather integration.

Provides multi-hop retrieval across regional CSV, crop JSON, and PDF treatment rules.
Synthesizes grounded agronomic answers with verified citations and live weather baselines.
"""

import csv
from functools import lru_cache
import json
import logging
import os
from pathlib import Path
from typing import Any

from app.config import generate_text_with_llm, get_settings
from app.rag.chunkers import chunk_pdf_file
from app.rag.query_transform import transform_query
from app.rag.schemas import (
    CitationItem,
    LiveWeatherInfo,
    RagQueryRequest,
    RagQueryResponse,
    RecommendedCropCard,
    RetrievedChunk,
)
from app.rag.vector_store import GardenVectorStore, get_vector_store

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_api_fallback_cache() -> dict[str, Any]:
    """Load pre-verified Open-Meteo and GBIF fallback fixtures from cache."""
    settings = get_settings()
    cache_path = settings.data_dir / "demo_fixtures" / "api_fallback_cache.json"
    if cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


@lru_cache(maxsize=1)
def _get_suburbs_lookup() -> dict[str, dict[str, Any]]:
    """Load regional soil and climate CSV into a dictionary keyed by lowercase suburb name."""
    settings = get_settings()
    csv_path = settings.data_dir / "regional_soil_and_climate.csv"
    lookup: dict[str, dict[str, Any]] = {}
    if csv_path.exists():
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=1):
                name = row.get("suburb", "").strip()
                if name:
                    key = name.lower()
                    row_copy = dict(row)
                    row_copy["row_number"] = row_idx
                    lookup[key] = row_copy
    return lookup


@lru_cache(maxsize=1)
def _get_crops_guide() -> list[dict[str, Any]]:
    """Load all 40 crops from crop_planting_guide.json."""
    settings = get_settings()
    json_path = settings.data_dir / "crop_planting_guide.json"
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    return []


@lru_cache(maxsize=1)
def _get_pdf_chunks() -> list[Any]:
    """Load parsed PDF chunks from soil_treatment_and_watering_rules.pdf."""
    settings = get_settings()
    pdf_path = settings.data_dir / "soil_treatment_and_watering_rules.pdf"
    if pdf_path.exists():
        return chunk_pdf_file(pdf_path)
    return []


def fetch_live_suburb_weather(suburb: str | None) -> LiveWeatherInfo:
    """Fetch live weather observation and regional soil baseline for a suburb.

    Defaults to Woodstock if suburb is not specified. Queries Open-Meteo HTTP API
    when ENABLE_LIVE_WEATHER_HTTP is set to 1; otherwise uses deterministic fixture cache.
    """
    canonical_suburb = suburb.strip() if suburb and suburb.strip() else "Woodstock"
    suburbs_map = _get_suburbs_lookup()
    sub_row = suburbs_map.get(canonical_suburb.lower())

    if not sub_row and suburbs_map:
        canonical_suburb = "Woodstock"
        sub_row = suburbs_map.get("woodstock", {})

    sub_row = sub_row or {}
    soil_type = sub_row.get("soil_type", "sandy_loam")
    baseline_ph_range = sub_row.get("baseline_ph_range", "5.3 - 5.8")
    lat = float(sub_row.get("latitude", -33.9268))
    lon = float(sub_row.get("longitude", 18.4462))

    cache = _get_api_fallback_cache()
    weather_cache = cache.get("weather_by_suburb", {})
    cached_entry = weather_cache.get(canonical_suburb.lower(), {})

    temperature_c = float(cached_entry.get("temperature_c", 21.4))
    condition = str(cached_entry.get("condition", "Partly Cloudy"))
    humidity_pct = int(cached_entry.get("humidity_pct", 64))
    precipitation_mm = float(cached_entry.get("precipitation_mm", 0.0))
    soil_moisture = float(cached_entry.get("soil_moisture", 0.24))
    frost_risk_7d = bool(cached_entry.get("frost_risk_7d", False))

    if os.getenv("ENABLE_LIVE_WEATHER_HTTP", "0") == "1":
        try:
            import httpx

            resp = httpx.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
                    "daily": "temperature_2m_min",
                    "timezone": "Africa/Johannesburg",
                },
                timeout=2.0,
            )
            if resp.status_code == 200:
                payload = resp.json()
                current_data = payload.get("current", {})
                daily_data = payload.get("daily", {})
                temperature_c = float(current_data.get("temperature_2m", temperature_c))
                humidity_pct = int(current_data.get("relative_humidity_2m", humidity_pct))
                precipitation_mm = float(current_data.get("precipitation", precipitation_mm))
                min_temps = daily_data.get("temperature_2m_min", [])
                if min_temps:
                    frost_risk_7d = any(float(t) <= 2.0 for t in min_temps)

                code = current_data.get("weather_code", 0)
                if code == 0:
                    condition = "Clear Sky"
                elif code in (1, 2):
                    condition = "Partly Cloudy"
                elif code == 3:
                    condition = "Overcast"
                elif code in (51, 53, 55, 61, 63, 65, 80, 81):
                    condition = "Light Rain"
                elif code in (95, 96, 99):
                    condition = "Thunderstorm"
        except Exception as exc:
            logger.info("Live Open-Meteo HTTP lookup skipped or failed; using cache: %s", exc)

    return LiveWeatherInfo(
        suburb=sub_row.get("suburb", canonical_suburb),
        temperature_c=temperature_c,
        condition=condition,
        humidity_pct=humidity_pct,
        precipitation_mm=precipitation_mm,
        soil_moisture=soil_moisture,
        frost_risk_7d=frost_risk_7d,
        baseline_ph_range=baseline_ph_range,
        soil_type=soil_type,
        source="Open-Meteo API & Regional Datasets",
    )


def _parse_chunk_fields(text: str) -> dict[str, str]:
    """Parse 'col: val | col2: val2' pairs from a structured chunk text."""
    body = text.split("] ", 1)[-1] if "] " in text else text
    fields: dict[str, str] = {}
    for part in body.split(" | "):
        if ":" in part:
            k, v = part.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields


def _ph_matches_bracket(ph: float, bracket: str) -> bool:
    """Check whether a measured pH falls within a 'min - max' bracket string."""
    parts = [p.strip() for p in bracket.split("-")]
    if len(parts) == 2:
        try:
            low = float(parts[0])
            high = float(parts[1])
            return low <= ph <= high
        except ValueError:
            return False
    return False


def _find_matching_treatment_rule(
    soil_type: str,
    effective_ph: float,
) -> tuple[dict[str, Any] | None, str | None]:
    """Find matching Table 1 row in soil_treatment_and_watering_rules.pdf across all 5 soil types.

    Table 1 contains amendment brackets:
    - 4.5 - 5.0: Dolomitic Lime
    - 5.0 - 5.5: Agricultural Lime
    - 5.5 - 6.0: Agricultural Lime
    - 6.0 - 7.2: Balanced optimal range, no chemical amendment required (returns None, None)
    - 7.2 - 7.8: Elemental Sulfur
    - 7.8 - 8.5: Elemental Sulfur
    """
    pdf_chunks = _get_pdf_chunks()
    normalized_soil = soil_type.lower().strip()

    # Determine target bracket using half-open intervals
    if effective_ph < 5.0:
        target_bracket = "4.5 - 5.0"
    elif 5.0 <= effective_ph < 5.5:
        target_bracket = "5.0 - 5.5"
    elif 5.5 <= effective_ph < 6.0:
        target_bracket = "5.5 - 6.0"
    elif 6.0 <= effective_ph < 7.2:
        return None, None
    elif 7.2 <= effective_ph < 7.8:
        target_bracket = "7.2 - 7.8"
    else:
        target_bracket = "7.8 - 8.5"

    for c in pdf_chunks:
        if c.metadata.get("page_number") == 1:
            chunk_soil = str(c.metadata.get("soil_type", "")).lower()
            if chunk_soil == normalized_soil:
                fields = _parse_chunk_fields(c.text)
                bracket = fields.get("current_ph_bracket", "").strip()
                if bracket == target_bracket:
                    return {
                        "rule_id": fields.get("rule_id", "RULE-PH-02"),
                        "dosage": fields.get("dosage_g_per_m2", "150"),
                        "amendment": fields.get("amendment_type", "Agricultural Lime"),
                        "target_shift": fields.get("target_ph_shift", "optimal 6.0-6.8"),
                        "chunk_id": c.chunk_id,
                    }, c.locator

    return None, None


def _build_grounded_answer(
    question: str,
    suburb: str,
    soil_type: str,
    baseline_ph: float,
    baseline_ph_range: str,
    effective_ph: float,
    weather: LiveWeatherInfo,
    crops: list[dict[str, Any]],
    treatment_rule: dict[str, Any] | None,
    treatment_locator: str | None,
    csv_locator: str,
    pdf_watering_locator: str,
) -> str:
    """Build deterministic grounded synthesis citing all 3 source files explicitly."""
    frost_text = "low frost risk over the next 7 days" if not weather.frost_risk_7d else "elevated frost risk"
    
    crops_text_list: list[str] = []
    for c in crops:
        c_name = c["crop_name"]
        sci = c.get("scientific_name", "")
        ph_min = float(c.get("soil_ph_min", 6.0))
        ph_max = float(c.get("soil_ph_max", 7.0))
        water = c.get("water_mm_per_week", 30)
        if effective_ph < ph_min:
            ph_compatibility = f"Your current soil pH of {effective_ph} is below the optimal threshold for {c_name}."
        elif effective_ph > ph_max:
            ph_compatibility = f"Your current soil pH of {effective_ph} is above the optimal threshold for {c_name}."
        else:
            ph_compatibility = f"{c_name} will thrive directly at your soil pH of {effective_ph}."

        crops_text_list.append(
            f"{c_name} ({sci}) requires an optimal soil pH of {ph_min} - {ph_max} "
            f"and {water} mm of water per week [crop_planting_guide.json · {c_name}]. "
            f"{ph_compatibility}"
        )

    crops_summary = " ".join(crops_text_list)

    if treatment_rule and treatment_locator:
        dosage = treatment_rule.get("dosage", "150")
        amendment = treatment_rule.get("amendment", "Agricultural Lime")
        treatment_sentence = (
            f"To adjust {soil_type} soil from pH {effective_ph} into the optimal 6.0 - 6.8 range, "
            f"apply {dosage}g/m2 {amendment} incorporated into the top 20cm of soil 2 weeks before "
            f"planting [soil_treatment_and_watering_rules.pdf · {treatment_locator}]."
        )
    else:
        treatment_sentence = (
            f"Native {soil_type} soil at pH {effective_ph} is already within the balanced 6.0 - 7.2 range, "
            f"so no chemical lime or sulfur amendment is required [soil_treatment_and_watering_rules.pdf · Page 1, Table 1]."
        )

    return (
        f"In {suburb}, the native soil type is {soil_type} with a regional baseline soil pH "
        f"of {baseline_ph} (typical range {baseline_ph_range}) [regional_soil_and_climate.csv · {csv_locator}]. "
        f"Live conditions show {weather.temperature_c:.1f} C, {weather.condition}, "
        f"{weather.humidity_pct}% humidity, and {frost_text} [Open-Meteo API & Regional Datasets].\n\n"
        f"{crops_summary}\n\n"
        f"{treatment_sentence} "
        f"For irrigation, maintain baseline watering adjusted for ambient temperature brackets "
        f"[soil_treatment_and_watering_rules.pdf · {pdf_watering_locator}]."
    )


def run_rag_query(
    request: RagQueryRequest,
    vector_store: GardenVectorStore | None = None,
) -> RagQueryResponse:
    """Execute multi-hop structured RAG pipeline across regional CSV, crop JSON, and PDF rules."""
    store = vector_store or get_vector_store()
    store.ensure_indexed()

    # 1. Transform query and resolve conversational pronouns
    qt = transform_query(request.question, request.chat_history)

    # 2. Fetch live weather and soil baseline
    weather = fetch_live_suburb_weather(qt.detected_suburb)
    suburb = weather.suburb
    soil_type = weather.soil_type

    suburbs_map = _get_suburbs_lookup()
    sub_row = suburbs_map.get(suburb.lower(), {})
    baseline_ph = float(sub_row.get("baseline_soil_ph", 5.5))
    baseline_ph_range = str(sub_row.get("baseline_ph_range", weather.baseline_ph_range))
    csv_row_number = sub_row.get("row_number", 1)
    csv_locator = f"Row {csv_row_number}"

    # Determine effective soil pH: user detected or suburb baseline
    effective_ph = qt.detected_soil_ph if qt.detected_soil_ph is not None else baseline_ph

    # 3. Multi-Source Targeted Retrieval (Never apply a global suburb filter across all sources)
    candidate_chunks: dict[str, RetrievedChunk] = {}

    def add_candidates(chunks: list[RetrievedChunk]) -> None:
        for chunk in chunks:
            if chunk.chunk_id not in candidate_chunks or chunk.similarity > candidate_chunks[chunk.chunk_id].similarity:
                candidate_chunks[chunk.chunk_id] = chunk

    # a) Suburb retrieval from regional CSV
    if qt.detected_suburb:
        add_candidates(store.search(qt.detected_suburb, top_k=2, where={"suburb": qt.detected_suburb.lower()}))
    else:
        add_candidates(store.search(suburb, top_k=2, where={"suburb": suburb.lower()}))

    # b) Crop retrieval from crop JSON
    if qt.detected_crops:
        for crop in qt.detected_crops:
            add_candidates(store.search(crop, top_k=2, where={"crop_name": crop.lower()}))
    else:
        add_candidates(store.search(qt.resolved_question, top_k=2, where={"source_file": "crop_planting_guide.json"}))

    # c) Sub-query retrieval for each targeted reference source
    for sq in qt.sub_queries:
        add_candidates(store.search(sq.query, top_k=3, where={"source_file": sq.target_source}))

    # d) PDF Soil Treatment and Watering Rules retrieval
    pdf_query = f"{soil_type} lime sulfur pH {effective_ph} application dosage"
    add_candidates(store.search(pdf_query, top_k=3, where={"source_file": "soil_treatment_and_watering_rules.pdf"}))

    # Boost the exact matched PDF Table 1 rule chunk for (soil_type, effective_ph) if amendment needed
    treatment_rule, treatment_locator = _find_matching_treatment_rule(soil_type, effective_ph)
    if treatment_rule:
        rule_chunk_id = treatment_rule.get("chunk_id", "")
        for c in _get_pdf_chunks():
            if c.chunk_id == rule_chunk_id:
                candidate_chunks[rule_chunk_id] = RetrievedChunk(
                    chunk_id=c.chunk_id,
                    source_file=c.source_file,
                    locator=c.locator,
                    similarity=0.96,
                    text=c.text,
                    metadata=c.metadata,
                )
                break

    # Categorize candidates by source file to guarantee presence of all 3 sources
    csv_candidates = [c for c in candidate_chunks.values() if c.source_file == "regional_soil_and_climate.csv"]
    json_candidates = [c for c in candidate_chunks.values() if c.source_file == "crop_planting_guide.json"]
    pdf_candidates = [c for c in candidate_chunks.values() if c.source_file == "soil_treatment_and_watering_rules.pdf"]

    csv_candidates.sort(key=lambda x: x.similarity, reverse=True)
    json_candidates.sort(key=lambda x: x.similarity, reverse=True)
    pdf_candidates.sort(key=lambda x: x.similarity, reverse=True)

    # Fallback queries if any source has insufficient chunks
    if not csv_candidates:
        csv_candidates = store.search(f"{suburb} climate soil", top_k=2, where={"source_file": "regional_soil_and_climate.csv"})
    if len(json_candidates) < 2:
        extra_json = store.search("Spinach leafy vegetables planting guide", top_k=3, where={"source_file": "crop_planting_guide.json"})
        for c in extra_json:
            if c.chunk_id not in [x.chunk_id for x in json_candidates]:
                json_candidates.append(c)
    if len(pdf_candidates) < 2:
        extra_pdf = store.search("Agricultural lime dosage watering rules", top_k=3, where={"source_file": "soil_treatment_and_watering_rules.pdf"})
        for c in extra_pdf:
            if c.chunk_id not in [x.chunk_id for x in pdf_candidates]:
                pdf_candidates.append(c)

    # Guarantee selection: at least 1 CSV, at least 2 JSON, at least 2 PDF, capped at 6 total
    selected_chunks: list[RetrievedChunk] = []
    selected_chunk_ids: set[str] = set()

    for c in csv_candidates[:1]:
        selected_chunks.append(c)
        selected_chunk_ids.add(c.chunk_id)

    for c in json_candidates[:2]:
        if c.chunk_id not in selected_chunk_ids:
            selected_chunks.append(c)
            selected_chunk_ids.add(c.chunk_id)

    for c in pdf_candidates[:2]:
        if c.chunk_id not in selected_chunk_ids:
            selected_chunks.append(c)
            selected_chunk_ids.add(c.chunk_id)

    # Fill remaining slot up to 6 chunks with highest similarity candidate
    remaining = [c for c in candidate_chunks.values() if c.chunk_id not in selected_chunk_ids]
    remaining.sort(key=lambda x: x.similarity, reverse=True)
    for c in remaining:
        if len(selected_chunks) >= 6:
            break
        selected_chunks.append(c)
        selected_chunk_ids.add(c.chunk_id)

    selected_chunks.sort(key=lambda x: x.similarity, reverse=True)

    # 4. Action banner construction
    if treatment_rule and treatment_locator:
        dosage = treatment_rule["dosage"]
        amendment = treatment_rule["amendment"]
        action_verb = "raise" if "Lime" in amendment else "lower"
        action_banner = (
            f"Action: Apply {dosage}g/m2 {amendment} to {action_verb} {soil_type} "
            f"soil pH from {effective_ph} to optimal 6.0-6.8 "
            f"(see [soil_treatment_and_watering_rules.pdf · {treatment_locator}])."
        )
    else:
        action_banner = (
            f"Optimal Soil pH: {soil_type} soil at pH {effective_ph} is within the 6.0–7.2 range; "
            f"no lime or sulfur amendment is required (see [soil_treatment_and_watering_rules.pdf · Page 1, Table 1])."
        )

    # 5. Recommended crops construction
    guide_crops = _get_crops_guide()
    guide_by_name = {c["crop_name"].lower(): c for c in guide_crops}

    recommended_raw: list[dict[str, Any]] = []
    # Start with detected crops
    for crop_name in qt.detected_crops:
        c_entry = guide_by_name.get(crop_name.lower())
        if c_entry and c_entry not in recommended_raw:
            recommended_raw.append(c_entry)

    # Add crops from retrieved JSON chunks
    for chunk in json_candidates:
        crop_id = chunk.metadata.get("crop_id")
        for c in guide_crops:
            if c.get("crop_id") == crop_id and c not in recommended_raw:
                recommended_raw.append(c)
                break

    # Ensure suitable companion or acid/neutral crop is present
    if len(recommended_raw) < 3:
        for c in guide_crops:
            if c not in recommended_raw:
                recommended_raw.append(c)
                if len(recommended_raw) >= 3:
                    break

    recommended_cards: list[RecommendedCropCard] = []
    for c in recommended_raw[:3]:
        card = RecommendedCropCard(
            crop_name=c["crop_name"],
            scientific_name=c.get("scientific_name", ""),
            description=c.get("description", ""),
            optimal_ph=f"{c.get('soil_ph_min', 6.0)} - {c.get('soil_ph_max', 7.0)}",
            water_mm_per_week=int(c.get("water_mm_per_week", 30)),
            citation=f"[crop_planting_guide.json · {c['crop_name']}]",
        )
        recommended_cards.append(card)

    # 6. Citations list construction
    citations_seen: set[tuple[str, str]] = set()
    citations: list[CitationItem] = []
    for chunk in selected_chunks:
        key = (chunk.source_file, chunk.locator)
        if key not in citations_seen:
            citations_seen.add(key)
            citations.append(
                CitationItem(
                    source_file=chunk.source_file,
                    locator=chunk.locator,
                    label=f"[{chunk.source_file} · {chunk.locator}]",
                )
            )

    # 7. Grounded Answer Synthesis
    pdf_watering_locator = "Page 2, Table 1, Row 2"
    for chunk in pdf_candidates:
        if chunk.metadata.get("page_number") == 2:
            pdf_watering_locator = chunk.locator
            break

    deterministic_answer = _build_grounded_answer(
        question=request.question,
        suburb=suburb,
        soil_type=soil_type,
        baseline_ph=baseline_ph,
        baseline_ph_range=baseline_ph_range,
        effective_ph=effective_ph,
        weather=weather,
        crops=recommended_raw[:3],
        treatment_rule=treatment_rule,
        treatment_locator=treatment_locator,
        csv_locator=csv_locator,
        pdf_watering_locator=pdf_watering_locator,
    )

    system_prompt = (
        "You are an agronomy advisor for Cape Town gardeners. Synthesize a concise, "
        "accurate answer using the provided context chunks. You MUST cite all three "
        "reference files explicitly in your text: [regional_soil_and_climate.csv · locator], "
        "[crop_planting_guide.json · Crop], and [soil_treatment_and_watering_rules.pdf · locator]. "
        "State the exact dosage in g/m2 for soil treatment and cite live weather conditions."
    )

    context_str = "\n\n".join(
        f"Chunk [{c.source_file} · {c.locator}]:\n{c.text}" for c in selected_chunks
    )
    user_prompt = (
        f"Question: {request.question}\n\n"
        f"Resolved Question: {qt.resolved_question}\n"
        f"Live Weather: {weather.suburb}, {weather.temperature_c} C, {weather.condition}, "
        f"Frost Risk: {weather.frost_risk_7d}\n\n"
        f"Reference Context:\n{context_str}\n\n"
        f"Grounded Reference Answer:\n{deterministic_answer}"
    )

    llm_answer, _ = generate_text_with_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        fallback_fn=lambda: deterministic_answer,
    )

    # Strict citation verification: if LLM omits any of the 3 sources, use deterministic answer
    required_citations = [
        "regional_soil_and_climate.csv",
        "crop_planting_guide.json",
        "soil_treatment_and_watering_rules.pdf",
    ]
    if not all(src in llm_answer for src in required_citations):
        final_answer = deterministic_answer
    else:
        final_answer = llm_answer

    # Prepend suburb explanation if question didn't name a known suburb
    suburb_note = ""
    if not qt.detected_suburb:
        suburb_note = (
            "Note: No suburb was specified in your question, so Woodstock is used as the regional baseline. "
            "Specify your suburb (e.g. Durbanville, Constantia) for local soil and weather data.\n\n"
        )
    elif qt.detected_suburb.strip().lower() != weather.suburb.strip().lower():
        suburb_note = (
            f"Note: '{qt.detected_suburb}' is not in our regional soil dataset, so Woodstock is used as the baseline. "
            "Choose a supported Western Cape suburb for tailored local guidance.\n\n"
        )

    final_answer = suburb_note + final_answer

    return RagQueryResponse(
        answer=final_answer,
        action_banner=action_banner,
        query_transform=qt,
        live_weather=weather,
        recommended_crops=recommended_cards,
        retrieved_chunks=selected_chunks,
        citations=citations,
    )
