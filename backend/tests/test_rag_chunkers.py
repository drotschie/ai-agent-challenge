"""Unit tests for Part 1 structure-aware chunkers and vector store."""

from pathlib import Path

import pytest

from app.config import get_settings
from app.rag.chunkers import (
    chunk_csv_file,
    chunk_json_file,
    chunk_pdf_file,
    load_and_chunk_all_sources,
)
from app.rag.vector_store import GardenVectorStore


@pytest.fixture
def data_dir() -> Path:
    """Return backend data directory containing source fixtures."""
    return get_settings().data_dir


def test_csv_chunker_preserves_headers_and_woodstock_row_1(data_dir: Path) -> None:
    """Verify CSV chunker produces 40 chunks with Woodstock at Row 1 and intact headers."""
    csv_path = data_dir / "regional_soil_and_climate.csv"
    chunks = chunk_csv_file(csv_path)

    assert len(chunks) == 40

    # Row 1 is Woodstock
    row_1 = chunks[0]
    assert row_1.locator == "Row 1"
    assert row_1.chunk_id == "regional_soil_and_climate.csv:row_1"
    assert row_1.metadata["suburb"] == "woodstock"
    assert row_1.metadata["suburb_display"] == "Woodstock"
    assert row_1.metadata["soil_type"] == "sandy_loam"
    assert row_1.metadata["baseline_soil_ph"] == 5.5
    assert row_1.metadata["baseline_ph_range"] == "5.3 - 5.8"
    assert row_1.metadata["row_number"] == 1

    # Every chunk contains column labels and proper citation preamble
    for c in chunks:
        assert "[Source: regional_soil_and_climate.csv | Row" in c.text
        assert "suburb:" in c.text
        assert "soil_type:" in c.text
        assert "baseline_soil_ph:" in c.text
        assert c.chunk_id.startswith("regional_soil_and_climate.csv:row_")
        assert c.metadata["source_file"] == "regional_soil_and_climate.csv"


def test_json_chunker_preserves_schema_and_40_crops(data_dir: Path) -> None:
    """Verify JSON chunker produces 40 crop chunks with Spinach parameters verified."""
    json_path = data_dir / "crop_planting_guide.json"
    chunks = chunk_json_file(json_path)

    assert len(chunks) == 40

    spinach_chunks = [c for c in chunks if c.locator == "Spinach"]
    assert len(spinach_chunks) == 1
    spinach = spinach_chunks[0]

    assert spinach.locator == "Spinach"
    assert spinach.chunk_id == "crop_planting_guide.json:CROP-01"
    assert spinach.metadata["crop_id"] == "CROP-01"
    assert spinach.metadata["crop_name"] == "spinach"
    assert spinach.metadata["crop_name_display"] == "Spinach"
    assert spinach.metadata["soil_ph_min"] == 6.0
    assert spinach.metadata["soil_ph_max"] == 7.0
    assert spinach.metadata["water_mm_per_week"] == 30
    assert spinach.metadata["frost_tolerant"] is True

    assert "scientific_name: Spinacia oleracea" in spinach.text
    assert "[Source: crop_planting_guide.json | Spinach]" in spinach.text


def test_pdf_chunker_extracts_both_tables_with_headers(data_dir: Path) -> None:
    """Verify PDF chunker extracts 45 rows across both tables with RULE-PH-02 verified."""
    pdf_path = data_dir / "soil_treatment_and_watering_rules.pdf"
    chunks = chunk_pdf_file(pdf_path)

    assert len(chunks) == 45

    table_1_chunks = [c for c in chunks if c.metadata.get("page_number") == 1]
    table_2_chunks = [c for c in chunks if c.metadata.get("page_number") == 2]

    assert len(table_1_chunks) == 25
    assert len(table_2_chunks) == 20

    # Page 1 Table 1 Row 2 is RULE-PH-02 (index 1 of table_1_chunks)
    row_2 = table_1_chunks[1]
    assert row_2.locator == "Page 1, Table 1, Row 2"
    assert row_2.chunk_id == "soil_treatment_and_watering_rules.pdf:p1_t1_r2"
    assert row_2.metadata["rule_id"] == "RULE-PH-02"
    assert row_2.metadata["soil_type"] == "sandy_loam"
    assert "RULE-PH-02" in row_2.text
    assert "sandy_loam" in row_2.text
    assert "150" in row_2.text
    assert "Agricultural Lime" in row_2.text

    # Every chunk includes column labels
    for c in table_1_chunks:
        assert "rule_id:" in c.text
        assert "soil_type:" in c.text
        assert "dosage_g_per_m2:" in c.text

    for c in table_2_chunks:
        assert "rule_id:" in c.text
        assert "temp_bracket_c:" in c.text
        assert "weekly_water_adjustment_mm:" in c.text


def test_vector_store_cosine_indexing_and_filtered_search(data_dir: Path) -> None:
    """Verify ephemeral vector store indexes 125 chunks and executes filtered searches."""
    all_chunks = load_and_chunk_all_sources(data_dir)
    assert len(all_chunks) == 125

    store = GardenVectorStore(ephemeral=True)
    indexed = store.index_chunks(all_chunks)
    assert indexed == 125
    assert store.count() == 125

    # 1. Unfiltered search
    unfiltered = store.search("Woodstock sandy_loam soil lime dosage", top_k=5)
    assert len(unfiltered) > 0
    for item in unfiltered:
        assert 0.0 <= item.similarity <= 1.0
        assert item.text
        assert item.chunk_id
        assert item.source_file
        assert item.locator

    # 2. Filtered search: CSV regional soil & climate
    csv_results = store.search(
        "Woodstock sandy loam",
        top_k=3,
        where={"source_file": "regional_soil_and_climate.csv"},
    )
    assert len(csv_results) > 0
    assert all(r.source_file == "regional_soil_and_climate.csv" for r in csv_results)
    assert all(0.0 <= r.similarity <= 1.0 for r in csv_results)

    # 3. Filtered search: JSON crop planting guide
    json_results = store.search(
        "Spinach leafy greens acid soil",
        top_k=3,
        where={"source_file": "crop_planting_guide.json"},
    )
    assert len(json_results) > 0
    assert all(r.source_file == "crop_planting_guide.json" for r in json_results)
    assert all(0.0 <= r.similarity <= 1.0 for r in json_results)

    # 4. Filtered search: PDF soil treatment & watering rules
    pdf_results = store.search(
        "Agricultural Lime dosage 150g sandy loam",
        top_k=3,
        where={"source_file": "soil_treatment_and_watering_rules.pdf"},
    )
    assert len(pdf_results) > 0
    assert all(
        r.source_file == "soil_treatment_and_watering_rules.pdf" for r in pdf_results
    )
    assert all(0.0 <= r.similarity <= 1.0 for r in pdf_results)
