"""Calendar tool adapter for fetching scheduled planting appointments.

Supports dual modes:
1. Google Calendar REST API using OAuth refresh tokens.
2. Local demo fixtures from backend/data/demo_fixtures/demo_calendar_events.json.
"""

import json
import logging
from pathlib import Path
import httpx

from app.agent.schemas import CalendarEvent
from app.config import get_settings, has_valid_key

logger = logging.getLogger(__name__)


def fetch_calendar_events(mode: str = "demo") -> tuple[list[CalendarEvent], str]:
    """Fetch calendar events from Google Calendar API or local demo fixture.

    Args:
        mode: Operation mode, either 'demo' or 'google_oauth'.

    Returns:
        tuple[list[CalendarEvent], str]: List of parsed calendar events and the mode used.
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
                events_response = httpx.get(
                    f"https://www.googleapis.com/calendar/v3/calendars/{settings.google_calendar_id}/events",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={"singleEvents": "true", "orderBy": "startTime"},
                    timeout=10.0,
                )
                if events_response.status_code == 200:
                    items = events_response.json().get("items", [])
                    events: list[CalendarEvent] = []
                    for item in items:
                        start = item.get("start", {})
                        sched_date = start.get("date") or (start.get("dateTime", "")[:10])
                        events.append(
                            CalendarEvent(
                                event_id=item.get("id", "EVT-REMOTE"),
                                scheduled_date=sched_date,
                                suburb=item.get("location", "Woodstock"),
                                plot_id=item.get("summary", "PLOT-W04"),
                                gardener_name=item.get("creator", {}).get("displayName", "Gardener"),
                                gardener_email=item.get("creator", {}).get("email", "gardener@capegardens.org.za"),
                                notes=item.get("description", ""),
                            )
                        )
                    if events:
                        return events, "google_oauth"
        except Exception as exc:
            logger.warning("Google Calendar API fetch failed, falling back to demo: %s", exc)

    fixture_path = settings.data_dir / "demo_fixtures" / "demo_calendar_events.json"
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)

    return [CalendarEvent(**e) for e in data], "demo"
