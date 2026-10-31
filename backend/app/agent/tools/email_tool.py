"""Email tool adapter for fetching and parsing gardener emails.

Supports dual modes:
1. Gmail REST API using OAuth refresh tokens.
2. Local demo fixtures from backend/data/demo_fixtures/demo_gardener_emails.json.

Includes deterministic regex and hint extraction with LLM fallback.
"""

import json
import logging
from pathlib import Path
import re
from typing import Any
import httpx

from app.agent.schemas import ExtractedEmailRecord, RawEmailMessage
from app.config import generate_json_with_llm, get_settings, has_valid_key
from app.rag.query_transform import CROP_ALIASES, get_known_crops, get_known_suburbs

logger = logging.getLogger(__name__)


def fetch_gardener_emails(mode: str = "demo") -> tuple[list[RawEmailMessage], str]:
    """Fetch gardener emails from Gmail API or local demo fixture.

    Args:
        mode: Operation mode, either 'demo' or 'google_oauth'.

    Returns:
        tuple[list[RawEmailMessage], str]: List of raw emails and the mode used.
    """
    settings = get_settings()

    if (
        mode == "google_oauth"
        and has_valid_key(settings.google_client_id)
        and has_valid_key(settings.google_client_secret)
        and has_valid_key(settings.google_refresh_token)
    ):
        try:
            token_response = httpx.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "refresh_token": settings.google_refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=10.0,
            )
            if token_response.status_code == 200:
                access_token = token_response.json().get("access_token")
                messages_res = httpx.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages?q=label:INBOX&maxResults=20",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                if messages_res.status_code == 200:
                    msg_list = messages_res.json().get("messages", [])
                    raw_emails: list[RawEmailMessage] = []
                    for m in msg_list:
                        msg_id = m.get("id", "")
                        detail_res = httpx.get(
                            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                            headers={"Authorization": f"Bearer {access_token}"},
                            timeout=10.0,
                        )
                        if detail_res.status_code == 200:
                            data = detail_res.json()
                            payload = data.get("payload", {})
                            headers = {
                                h.get("name", "").lower(): h.get("value", "")
                                for h in payload.get("headers", [])
                            }
                            snippet = data.get("snippet", "")
                            raw_emails.append(
                                RawEmailMessage(
                                    email_id=f"GMAIL-{msg_id[:8]}",
                                    sender_name=headers.get("from", "Unknown"),
                                    sender_email=headers.get("from", "unknown@capegardens.org.za"),
                                    received_at=headers.get("date", "2026-11-01T00:00:00Z"),
                                    subject=headers.get("subject", ""),
                                    body=snippet,
                                    parsed_hints={},
                                )
                            )
                    if raw_emails:
                        return raw_emails, "google_oauth"
        except Exception as exc:
            logger.warning("Gmail API fetch failed, falling back to demo: %s", exc)

    fixture_path = settings.data_dir / "demo_fixtures" / "demo_gardener_emails.json"
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)

    return [RawEmailMessage(**e) for e in data], "demo"


def _deterministic_extract(email: RawEmailMessage) -> dict[str, Any]:
    """Deterministically extract structured fields from parsed hints or regex.

    Sets missing fields strictly to None without guessing.
    """
    if email.parsed_hints:
        return {
            "email_id": email.email_id,
            "sender_name": email.sender_name,
            "sender_email": email.sender_email,
            "received_at": email.received_at,
            "planted_date_raw": email.parsed_hints.get("planted_date_raw"),
            "suburb": email.parsed_hints.get("suburb"),
            "plot_id": email.parsed_hints.get("plot_id"),
            "crop_name": email.parsed_hints.get("crop_name"),
            "species_scientific_raw": email.parsed_hints.get("species_scientific_raw"),
            "quantity_planted": email.parsed_hints.get("quantity_planted"),
            "measured_soil_ph": email.parsed_hints.get("measured_soil_ph"),
            "seed_batch_id": email.parsed_hints.get("seed_batch_id"),
        }

    # Fallback to direct regex extraction across subject and body
    text = f"{email.subject}\n{email.body}"

    # 1. Date extraction
    planted_date_raw: str | None = None
    iso_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if iso_match:
        planted_date_raw = iso_match.group(0)
    else:
        slash_match = re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", text)
        if slash_match:
            planted_date_raw = slash_match.group(0)
        else:
            month_first_match = re.search(
                r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b",
                text,
                re.IGNORECASE,
            )
            if month_first_match:
                planted_date_raw = month_first_match.group(0)
            else:
                day_first_match = re.search(
                    r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?),?\s+\d{4}\b",
                    text,
                    re.IGNORECASE,
                )
                if day_first_match:
                    planted_date_raw = day_first_match.group(0)

    # 2. Suburb extraction
    suburb: str | None = None
    for s in get_known_suburbs():
        if re.search(r"\b" + re.escape(s) + r"\b", text, re.IGNORECASE):
            suburb = s
            break

    # 3. Plot ID extraction
    plot_id: str | None = None
    plot_match = re.search(r"\bplot[-_\s]+([a-z0-9]+)\b", text, re.IGNORECASE)
    if plot_match:
        plot_id = f"PLOT-{plot_match.group(1).upper()}"
    else:
        direct_plot = re.search(r"\b(PLOT-[A-Z0-9]+)\b", text, re.IGNORECASE)
        if direct_plot:
            plot_id = direct_plot.group(1).upper()

    # 4. Crop name extraction
    crop_name: str | None = None
    for alias, canon in sorted(CROP_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(alias) + r"\b", text, re.IGNORECASE):
            crop_name = canon
            break
    if not crop_name:
        for c in get_known_crops():
            if re.search(r"\b" + re.escape(c) + r"\b", text, re.IGNORECASE):
                crop_name = c
                break

    # 5. Scientific species extraction
    species_scientific_raw: str | None = None
    paren_match = re.search(
        r"\((?:(?:scientific name|botanical name)\s+)?([A-Z][a-z]+ [a-z]+(?:\s+var\.\s+[a-z]+)?)\)",
        text,
        re.IGNORECASE,
    )
    if paren_match:
        species_scientific_raw = paren_match.group(1)
    else:
        label_match = re.search(
            r"(?:scientific name|botanical name|species listed as|species)\s+([A-Z][a-z]+ [a-z]+(?:\s+var\.\s+[a-z]+)?)",
            text,
            re.IGNORECASE,
        )
        if label_match:
            species_scientific_raw = label_match.group(1)

    # 6. Quantity planted
    quantity_planted: int | None = None
    qty_verb_match = re.search(
        r"\b(?:put in|transplant|transplanted|planted|seeded|seeding|planting)\s+(\d+)\b",
        text,
        re.IGNORECASE,
    )
    if qty_verb_match:
        quantity_planted = int(qty_verb_match.group(1))
    else:
        qty_unit_match = re.search(
            r"\b(\d+)\s*(?:units|seedlings|plants|mounds|seeds|rows)\b",
            text,
            re.IGNORECASE,
        )
        if qty_unit_match:
            quantity_planted = int(qty_unit_match.group(1))

    # 7. Measured soil pH
    measured_soil_ph: float | None = None
    if re.search(r"\b(?:forgot.*(?:ph|probe)|no ph|probe battery|battery was flat)\b", text, re.IGNORECASE):
        measured_soil_ph = None
    else:
        ph_match = re.search(
            r"\b(?:soil ph|ph)\s*(?:meter:?|tested at|reading is|measured|tested|confirmed|is|at|exactly)?\s*[:=]?\s*(\d+\.\d+)\b",
            text,
            re.IGNORECASE,
        )
        if not ph_match:
            ph_match = re.search(r"\b(\d+\.\d+)\s*(?:ph)\b", text, re.IGNORECASE)
        if ph_match:
            try:
                measured_soil_ph = float(ph_match.group(1))
            except ValueError:
                measured_soil_ph = None

    # 8. Seed batch ID
    seed_batch_id: str | None = None
    if re.search(r"\b(?:no batch label|no batch)\b", text, re.IGNORECASE):
        seed_batch_id = None
    else:
        batch_match = re.search(r"\b(BATCH-[A-Z0-9-]+)\b", text, re.IGNORECASE)
        if batch_match:
            seed_batch_id = batch_match.group(1).upper()

    return {
        "email_id": email.email_id,
        "sender_name": email.sender_name,
        "sender_email": email.sender_email,
        "received_at": email.received_at,
        "planted_date_raw": planted_date_raw,
        "suburb": suburb,
        "plot_id": plot_id,
        "crop_name": crop_name,
        "species_scientific_raw": species_scientific_raw,
        "quantity_planted": quantity_planted,
        "measured_soil_ph": measured_soil_ph,
        "seed_batch_id": seed_batch_id,
    }


def extract_record_from_email(email: RawEmailMessage) -> ExtractedEmailRecord:
    """Extract a structured ExtractedEmailRecord from a RawEmailMessage."""
    deterministic = _deterministic_extract(email)

    if email.parsed_hints:
        return ExtractedEmailRecord(**deterministic)

    def fallback_fn() -> dict[str, Any]:
        return deterministic

    system_prompt = (
        "You are an agricultural email entity extractor. Extract the planting report fields into JSON:\n"
        "- planted_date_raw (string or null)\n"
        "- suburb (string or null)\n"
        "- plot_id (string or null)\n"
        "- crop_name (string or null)\n"
        "- species_scientific_raw (string or null)\n"
        "- quantity_planted (integer or null)\n"
        "- measured_soil_ph (float or null)\n"
        "- seed_batch_id (string or null)\n\n"
        "CRITICAL RULE: If any field was not measured, forgotten, missing, or omitted, set it to null. "
        "Do NOT invent or extrapolate missing values."
    )
    user_prompt = f"Sender: {email.sender_name} <{email.sender_email}>\nSubject: {email.subject}\nBody: {email.body}"

    extracted_dict, _ = generate_json_with_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        fallback_fn=fallback_fn,
    )

    final_data = dict(deterministic)

    # Preserve deterministic regex matches first; use LLM extraction only for fields
    # that regex could not parse, while guarding against hallucinated pH/batch values.
    for k in (
        "planted_date_raw",
        "suburb",
        "plot_id",
        "crop_name",
        "species_scientific_raw",
        "quantity_planted",
        "measured_soil_ph",
        "seed_batch_id",
    ):
        if deterministic.get(k) is None and k not in ("measured_soil_ph", "seed_batch_id"):
            if extracted_dict.get(k) is not None:
                final_data[k] = extracted_dict[k]

    return ExtractedEmailRecord(**final_data)


def extract_all_emails(emails: list[RawEmailMessage]) -> list[ExtractedEmailRecord]:
    """Extract records from all raw email messages."""
    return [extract_record_from_email(email) for email in emails]
