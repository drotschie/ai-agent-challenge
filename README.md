# South African Gardener's Guide & Planting Verification Agent

A personal gardening assistant and planting log verification tool built around Western Cape soil surveys, crop guides, and local weather forecasts.

The project has two parts:
1. **Part 1 — Gardener's Guide (RAG)**: Answers practical gardening questions (what to plant in a specific suburb, whether soil pH needs lime or sulfur, and how much to water this week) by querying three local reference files (`crop_planting_guide.json`, `regional_soil_and_climate.csv`, and `soil_treatment_and_watering_rules.pdf`) together with live 7-day weather from Open-Meteo.
2. **Part 2 — Planting Log Verification Agent**: A 5-step LangGraph workflow that reads scheduled planting calendar entries and emailed planting notes, merges follow-up emails into single records, checks scientific plant names against the GBIF taxonomy API, checks measured soil pH against the crop guide and PDF treatment rules, and flags anything out of range.

---

## How It Works

### Part 1: Multi-Source RAG (`backend/app/rag/`)
- **Structure-Aware Chunking (`chunkers.py`)**: Instead of splitting files by character count, each source is parsed by its structure into 125 chunks with exact source locators:
  - `crop_planting_guide.json` -> 40 crop chunks (`[crop_planting_guide.json : Spinach]`)
  - `regional_soil_and_climate.csv` -> 40 suburb chunks (`[regional_soil_and_climate.csv : Row 1]`)
  - `soil_treatment_and_watering_rules.pdf` -> 45 table row chunks extracted with `pdfplumber` (`25` soil pH amendment rules from Table 1 and `20` climate watering rules from Table 2)
- **Local Vector Index (`vector_store.py`)**: Uses embedded `chromadb.PersistentClient` (`backend/data/chroma_db`) and FastEmbed (`BAAI/bge-small-en-v1.5`, 384 dimensions). No cloud vector database account or API key is needed.
- **Query Rewriting & Decomposition (`query_transform.py`)**: Resolves follow-up pronouns (`"there"`, `"that crop"`) from chat history, extracts suburb/crop/soil-pH entities, and splits the user's question into targeted sub-queries per file.
- **Grounded Synthesis (`pipeline.py`)**: Retrieves top chunks across all three files, attaches live Open-Meteo weather for the detected suburb, and synthesizes an answer with inline citations (`[source_file : locator]`).

### Part 2: Planting Verification Agent (`backend/app/agent/`)
The verification pipeline runs as a 5-node `StateGraph` (`graph.py`):
1. **`ingest_sources`**: Loads scheduled planting events and raw planting emails (either from the built-in 8-event / 10-email fixture set or via Google Calendar & Gmail OAuth).
2. **`clean_and_merge`**: Normalizes dates, quantities, soil pH values, and seed batch IDs (`normalizer.py`), and merges follow-up emails from the same sender and plot into a single canonical record while recording every change in `merge_audit_log`.
3. **`validate_rules`**: Checks each record's scientific name against the GBIF `/v1/species/match` endpoint (`gbif_tool.py`), looks up the suburb's soil type in `regional_soil_and_climate.csv`, checks the crop's ideal pH range in `crop_planting_guide.json`, and calculates exact lime or sulfur dosage (`g/m2`) from Table 1 of `soil_treatment_and_watering_rules.pdf`.
4. **`fetch_weather`**: Queries the Open-Meteo 7-day forecast (`weather_tool.py`) for each plot's suburb to check temperature, rain, and frost risk.
5. **`flag_and_audit`**: Marks each record as `VERIFIED`, `AUTO_CORRECTED` (for example, a GBIF species spelling correction or a follow-up quantity update), or `FLAGGED` (for example, `SOIL_PH_OUT_OF_RANGE`), and generates a CSV export.

### LLM & Offline Fallback Behavior
- **Primary LLM**: Groq (`llama-3.3-70b-versatile`) when `GROQ_API_KEY` is set.
- **Secondary LLM**: Google Gemini (`gemini-2.5-flash`) when `GEMINI_API_KEY` is set.
- **Offline / Keyless Fallback**: If neither API key is set, the backend falls back to deterministic Python synthesis using the retrieved chunks and rule tables, and uses a cached GBIF/Open-Meteo fallback file (`backend/data/demo_fixtures/api_fallback_cache.json`) if offline.

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 20+ and npm

### 1. Backend

```powershell
# Install Python dependencies
pip install -r backend/requirements.txt

# Generate the 3 structured datasets and demo fixtures (already committed under backend/data/)
python backend/scripts/fetch_real_garden_data.py

# Build the local ChromaDB vector index (125 chunks)
python backend/scripts/build_vector_index.py

# Run the 15-test suite
pytest backend/tests -v

# Start the FastAPI server on http://localhost:8000
uvicorn app.main:app --app-dir backend --reload --port 8000
```

### 2. Frontend

```powershell
# Install dependencies and start the Next.js app on http://localhost:3000
npm --prefix frontend install
npm --prefix frontend run dev
```

Open `http://localhost:3000` to use the three views:
- **Part 1: Gardener's Guide RAG**: Ask soil, crop, and watering questions, inspect the query rewrite breakdown, and view the retrieved ChromaDB chunks with cosine similarity scores.
- **Part 2: Planting Verification Agent**: Run the 5-step verification workflow, click any node in the React Flow graph to inspect its inputs and outputs, compare raw emails against cleaned records side by side, and download the verified CSV.
- **Data Sources**: Browse the raw JSON, CSV, and PDF rule tables directly in the UI.

---

## Environment Variables (`backend/.env`)

Copy `backend/.env.example` to `backend/.env`. All keys are optional for local evaluation:

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | `""` | Primary LLM (`llama-3.3-70b-versatile`) |
| `GEMINI_API_KEY` | `""` | Secondary fallback LLM (`gemini-2.5-flash`) |
| `AGENT_DEMO_MODE` | `true` | Uses the built-in 8 calendar events & 10 emails when `true` |
| `CHROMA_DB_DIR` | `data/chroma_db` | Path for the local embedded ChromaDB SQLite store |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed frontend origin(s) |
