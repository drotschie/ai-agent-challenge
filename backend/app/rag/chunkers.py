"""Structure-aware row and record chunkers for CSV, JSON, and PDF sources."""

import csv
import json
from pathlib import Path
from typing import Any

import pdfplumber

from app.config import get_settings
from app.rag.schemas import DocumentChunk


def chunk_csv_file(csv_path: Path) -> list[DocumentChunk]:
    """Chunk regional soil and climate CSV file row by row.

    Each row becomes an individually addressable chunk preserving column labels
    and structured scalar metadata for filtering.
    """
    chunks: list[DocumentChunk] = []
    source_file = csv_path.name

    with csv_path.open(mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_number, row in enumerate(reader, start=1):
            locator = f"Row {row_number}"
            chunk_id = f"{source_file}:row_{row_number}"
            labeled_pairs = " | ".join(f"{col}: {val}" for col, val in row.items())
            text = f"[Source: {source_file} | {locator}] {labeled_pairs}"

            try:
                baseline_ph = float(row.get("baseline_soil_ph", 0.0))
            except (ValueError, TypeError):
                baseline_ph = 0.0

            metadata: dict[str, Any] = {
                "source_file": source_file,
                "locator": locator,
                "row_number": row_number,
                "suburb": row.get("suburb", "").lower(),
                "suburb_display": row.get("suburb", ""),
                "province": row.get("province", "").lower(),
                "soil_type": row.get("soil_type", "").lower(),
                "baseline_soil_ph": baseline_ph,
                "baseline_ph_range": row.get("baseline_ph_range", ""),
                "frost_risk": row.get("frost_risk", "").lower(),
            }
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    source_file=source_file,
                    locator=locator,
                    text=text,
                    metadata=metadata,
                )
            )

    return chunks


def chunk_json_file(json_path: Path) -> list[DocumentChunk]:
    """Chunk crop planting guide JSON records record by record.

    Formats array fields as comma-separated values, links each attribute to its label,
    and sets locator to crop_name for clean citation formatting.
    """
    chunks: list[DocumentChunk] = []
    source_file = json_path.name

    with json_path.open(mode="r", encoding="utf-8") as f:
        records: list[dict[str, Any]] = json.load(f)

    for record in records:
        crop_id = str(record.get("crop_id", ""))
        crop_name = str(record.get("crop_name", ""))
        locator = crop_name
        chunk_id = f"{source_file}:{crop_id}"

        formatted_pairs: list[str] = []
        for key, val in record.items():
            if isinstance(val, list):
                formatted_val = ", ".join(str(item) for item in val)
            else:
                formatted_val = str(val)
            formatted_pairs.append(f"{key}: {formatted_val}")

        labeled_pairs = " | ".join(formatted_pairs)
        text = f"[Source: {source_file} | {locator}] {labeled_pairs}"

        try:
            soil_ph_min = float(record.get("soil_ph_min", 0.0))
        except (ValueError, TypeError):
            soil_ph_min = 0.0

        try:
            soil_ph_max = float(record.get("soil_ph_max", 0.0))
        except (ValueError, TypeError):
            soil_ph_max = 0.0

        try:
            water_mm = int(record.get("water_mm_per_week", 0))
        except (ValueError, TypeError):
            water_mm = 0

        metadata: dict[str, Any] = {
            "source_file": source_file,
            "locator": locator,
            "crop_id": crop_id,
            "crop_name": crop_name.lower(),
            "crop_name_display": crop_name,
            "scientific_name": str(record.get("scientific_name", "")),
            "soil_ph_min": soil_ph_min,
            "soil_ph_max": soil_ph_max,
            "water_mm_per_week": water_mm,
            "frost_tolerant": bool(record.get("frost_tolerant", False)),
        }
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                source_file=source_file,
                locator=locator,
                text=text,
                metadata=metadata,
            )
        )

    return chunks


def chunk_pdf_file(pdf_path: Path) -> list[DocumentChunk]:
    """Chunk vector-bordered tables from the soil treatment and watering PDF.

    Iterates through each page, extracts tables, pairs column headers to row values,
    and produces precise Page/Table/Row locators.
    """
    chunks: list[DocumentChunk] = []
    source_file = pdf_path.name

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table_num, table in enumerate(tables, start=1):
                if not table or len(table) < 2:
                    continue

                headers = [str(h).strip() if h is not None else "" for h in table[0]]
                for row_num, row in enumerate(table[1:], start=1):
                    locator = f"Page {page_num}, Table {table_num}, Row {row_num}"
                    chunk_id = f"{source_file}:p{page_num}_t{table_num}_r{row_num}"

                    row_clean = [str(val).strip() if val is not None else "" for val in row]
                    labeled_pairs = " | ".join(
                        f"{h}: {val}" for h, val in zip(headers, row_clean)
                    )
                    text = f"[Source: {source_file} | {locator}] {labeled_pairs}"

                    row_dict = dict(zip(headers, row_clean))
                    rule_id = row_dict.get("rule_id", "")
                    soil_type = row_dict.get("soil_type", "").lower()

                    metadata: dict[str, Any] = {
                        "source_file": source_file,
                        "locator": locator,
                        "page_number": page_num,
                        "table_number": table_num,
                        "row_number": row_num,
                        "rule_id": rule_id,
                        "soil_type": soil_type,
                    }
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            source_file=source_file,
                            locator=locator,
                            text=text,
                            metadata=metadata,
                        )
                    )

    return chunks


def load_and_chunk_all_sources(data_dir: Path | None = None) -> list[DocumentChunk]:
    """Load and chunk all three primary garden reference documents.

    Returns the complete list of 125 structured chunks across CSV, JSON, and PDF.
    """
    if data_dir is None:
        data_dir = get_settings().data_dir

    data_dir = Path(data_dir)
    csv_path = data_dir / "regional_soil_and_climate.csv"
    json_path = data_dir / "crop_planting_guide.json"
    pdf_path = data_dir / "soil_treatment_and_watering_rules.pdf"

    chunks: list[DocumentChunk] = []

    if csv_path.exists():
        chunks.extend(chunk_csv_file(csv_path))

    if json_path.exists():
        chunks.extend(chunk_json_file(json_path))

    if pdf_path.exists():
        chunks.extend(chunk_pdf_file(pdf_path))

    return chunks
