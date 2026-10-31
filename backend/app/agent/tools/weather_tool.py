"""Open-Meteo 7-day weather risk checker and agronomic advisory tool."""

from typing import Any

from app.rag.pipeline import _get_api_fallback_cache, fetch_live_suburb_weather


def verify_suburb_weather_risk(
    suburb: str,
    crop_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify 7-day weather risks (frost, extreme heat) for a suburb and optional crop.

    Fetches current weather and 7-day risk indicators via Open-Meteo or deterministic cache.
    """
    canonical_suburb = suburb.strip() if suburb and suburb.strip() else "Woodstock"
    live_weather = fetch_live_suburb_weather(canonical_suburb)

    cache = _get_api_fallback_cache()
    cached_sub = cache.get("weather_by_suburb", {}).get(canonical_suburb.lower(), {})
    max_temp_7d_c = float(cached_sub.get("max_temp_7d_c", live_weather.temperature_c))

    frost_warning = bool(live_weather.frost_risk_7d and not bool((crop_info or {}).get("frost_tolerant", True)))

    crop_optimal_max = float((crop_info or {}).get("optimal_temp_max_c", 35.0))
    heat_warning = bool(max_temp_7d_c > 36.0 and crop_optimal_max < 30.0)

    frost_status = "frost risk detected" if live_weather.frost_risk_7d else "no frost risk"
    weather_advisory = (
        f"{live_weather.temperature_c:.1f} C, "
        f"{live_weather.precipitation_mm:.1f}mm rain, "
        f"{frost_status} in {live_weather.suburb} over next 7 days"
    )

    return {
        "weather_advisory": weather_advisory,
        "frost_warning": frost_warning,
        "heat_warning": heat_warning,
        "soil_type": live_weather.soil_type,
        "temperature_c": live_weather.temperature_c,
    }
