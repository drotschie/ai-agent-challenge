/**
 * API types, client functions, and pre-seeded fallback fixtures
 * for the South African Gardener Guide and Verification System.
 */

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface SubQuery {
  target_source: string;
  query: string;
}

export interface QueryTransformResult {
  resolved_question: string;
  detected_suburb: string | null;
  detected_crops: string[];
  detected_soil_ph: number | null;
  sub_queries: SubQuery[];
}

export interface LiveWeatherInfo {
  suburb: string;
  temperature_c: number;
  condition: string;
  humidity_pct: number;
  precipitation_mm: number;
  soil_moisture: number;
  frost_risk_7d: boolean;
  baseline_ph_range: string;
  soil_type: string;
  source: string;
}

export interface RecommendedCropCard {
  crop_name: string;
  scientific_name: string;
  description: string;
  optimal_ph: string;
  water_mm_per_week: number;
  citation: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  source_file: string;
  locator: string;
  similarity: number;
  text: string;
  metadata?: Record<string, unknown>;
}

export interface CitationItem {
  source_file: string;
  locator: string;
  label: string;
}

export interface RagQueryRequest {
  question: string;
  chat_history?: ChatMessage[];
}

export interface RagQueryResponse {
  answer: string;
  action_banner: string | null;
  query_transform: QueryTransformResult;
  live_weather: LiveWeatherInfo | null;
  recommended_crops: RecommendedCropCard[];
  retrieved_chunks: RetrievedChunk[];
  citations: CitationItem[];
}

export interface CalendarEvent {
  event_id: string;
  scheduled_date: string;
  suburb: string;
  plot_id: string;
  gardener_name: string;
  gardener_email: string;
  notes: string;
}

export interface RawEmailMessage {
  email_id: string;
  sender_name: string;
  sender_email: string;
  received_at: string;
  subject: string;
  body: string;
  parsed_hints?: Record<string, unknown>;
}

export interface VerifiedPlantingRecord {
  record_id: string;
  source_email_ids: string[];
  raw_emails_before: RawEmailMessage[];
  merge_audit_log: string[];
  gardener_name: string;
  gardener_email: string;
  suburb: string;
  soil_type: string;
  plot_id: string;
  planted_date: string;
  crop_name: string;
  species_scientific_raw: string;
  species_scientific_verified: string;
  gbif_match_confidence: number;
  quantity_planted: number | null;
  measured_soil_ph: number | null;
  ideal_ph_range: string;
  seed_batch_id: string | null;
  soil_treatment_recommendation: string;
  weather_advisory: string;
  status: "VERIFIED" | "AUTO_CORRECTED" | "FLAGGED";
  flags: string[];
}

export interface WorkflowNodeTrace {
  node_id: string;
  step_number: number;
  label: string;
  status: "pending" | "running" | "completed" | "failed";
  duration_ms: number;
  summary_text: string;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
}

export interface AgentRunSummary {
  raw_emails_count: number;
  calendar_events_count: number;
  merged_records_count: number;
  verified_count: number;
  auto_corrected_count: number;
  flagged_count: number;
}

export interface AgentRunRequest {
  mode?: "demo" | "google_oauth";
}

export interface AgentRunResponse {
  run_id: string;
  mode_used: string;
  summary: AgentRunSummary;
  workflow_nodes: WorkflowNodeTrace[];
  records: VerifiedPlantingRecord[];
  csv_export: string;
}

export interface DataSourcesResponse {
  crops_json: Array<Record<string, unknown>>;
  suburbs_csv: Array<Record<string, unknown>>;
  pdf_tables: {
    table_1_soil_treatment: Array<Record<string, unknown>>;
    table_2_watering_rules: Array<Record<string, unknown>>;
  };
  demo_calendar_events: CalendarEvent[];
  demo_gardener_emails: RawEmailMessage[];
  technical_summary_md: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const INITIAL_RAG_RESPONSE: RagQueryResponse = {
  answer:
    "Based on regional soil analysis for Woodstock, the native soil is sandy_loam with a baseline pH between 5.3 and 5.8 [regional_soil_and_climate.csv : Row 1]. Spinach thrives in pH 6.0-7.0 and requires approximately 30 mm of water weekly [crop_planting_guide.json : Spinach]. To bring your current soil pH of 5.3 into the optimal range for spinach and companion crops, apply 150g/m2 of Agricultural Lime into the top 15cm of soil [soil_treatment_and_watering_rules.pdf : Page 1, Table 1, Row 2]. Given current Woodstock conditions (21.4°C and 0mm precipitation), maintain 5cm organic pine bark or straw mulch to suppress rapid evaporation from drying coastal winds [soil_treatment_and_watering_rules.pdf : Page 2, Table 2, Row 4].",
  action_banner:
    "Action: Apply 150g/m2 Agricultural Lime to raise sandy_loam soil pH from 5.3 to optimal 6.0-6.8.",
  query_transform: {
    resolved_question:
      "What vegetables grow well in Woodstock with soil pH 5.3, and how much agricultural lime is required?",
    detected_suburb: "Woodstock",
    detected_crops: ["Spinach", "Heirloom Tomato", "Potato"],
    detected_soil_ph: 5.3,
    sub_queries: [
      {
        target_source: "regional_soil_and_climate.csv",
        query: "Woodstock soil type baseline pH climate frost risk",
      },
      {
        target_source: "crop_planting_guide.json",
        query:
          "Spinach Heirloom Tomato Potato optimal soil pH range temperature Western Cape",
      },
      {
        target_source: "soil_treatment_and_watering_rules.pdf",
        query:
          "agricultural lime dosage g/m2 sandy_loam pH 5.3 to 6.5 watering adjustment",
      },
    ],
  },
  live_weather: {
    suburb: "Woodstock",
    temperature_c: 21.4,
    condition: "Partly Cloudy",
    humidity_pct: 64,
    precipitation_mm: 0.0,
    soil_moisture: 0.24,
    frost_risk_7d: false,
    baseline_ph_range: "5.3 - 5.8",
    soil_type: "sandy_loam",
    source: "Open-Meteo API & Regional Datasets",
  },
  recommended_crops: [
    {
      crop_name: "Spinach",
      scientific_name: "Spinacia oleracea",
      description:
        "Tolerates slightly acidic initial conditions but flourishes when soil is amended with lime to pH 6.0-7.0. Requires consistent irrigation and organic compost mulch in Cape summer heat.",
      optimal_ph: "6.0 - 7.0",
      water_mm_per_week: 30,
      citation: "[crop_planting_guide.json : Spinach]",
    },
    {
      crop_name: "Heirloom Tomato",
      scientific_name: "Solanum lycopersicum",
      description:
        "Thrives in sunny, well-draining sandy loam. Sensitive to calcium deficiency (blossom end rot) if pH dips below 5.8; the lime application directly supports robust root uptake.",
      optimal_ph: "6.0 - 6.8",
      water_mm_per_week: 35,
      citation: "[crop_planting_guide.json : Heirloom Tomato]",
    },
    {
      crop_name: "Potato",
      scientific_name: "Solanum tuberosum",
      description:
        "Naturally adapted to acidic soils (pH 5.0-6.0) with high scab resistance at lower pH. Ideal immediate planting choice before full lime reaction stabilizes.",
      optimal_ph: "5.0 - 6.0",
      water_mm_per_week: 25,
      citation: "[crop_planting_guide.json : Potato]",
    },
  ],
  retrieved_chunks: [
    {
      chunk_id: "regional_soil_and_climate.csv:row_1",
      source_file: "regional_soil_and_climate.csv",
      locator: "Row 1",
      similarity: 0.94,
      text: "[Source: regional_soil_and_climate.csv : Row 1] suburb: Woodstock | soil_type: sandy_loam | baseline_soil_ph: 5.5 | summer_rainfall_mm: 18 | winter_rainfall_mm: 82 | frost_risk: None | microclimate_notes: Well-draining urban coastal slope prone to summer drying winds.",
    },
    {
      chunk_id: "crop_planting_guide.json:spinach",
      source_file: "crop_planting_guide.json",
      locator: "Spinach",
      similarity: 0.89,
      text: "[Source: crop_planting_guide.json : Spinach] crop: Spinach | scientific_name: Spinacia oleracea | category: leafy_green | optimal_soil_ph: 6.0-7.0 | planting_season: Year-round (Cape autumn/spring peak) | water_requirement: 30 mm/week | companion_plants: Strawberries, Onions.",
    },
    {
      chunk_id: "soil_treatment_and_watering_rules.pdf:table_1_rule_2",
      source_file: "soil_treatment_and_watering_rules.pdf",
      locator: "Page 1, Table 1, Row 2",
      similarity: 0.87,
      text: "[Source: soil_treatment_and_watering_rules.pdf : Page 1, Table 1, Row 2] rule_id: STR-002 | soil_type: sandy_loam | current_ph_bracket: 5.0 - 5.5 | target_ph_shift: +0.8 to +1.0 | amendment_type: Agricultural Lime | dosage_g_per_m2: 150 | application_notes: Work into top 15cm soil 2-3 weeks prior to planting; water deeply.",
    },
    {
      chunk_id: "soil_treatment_and_watering_rules.pdf:table_2_rule_4",
      source_file: "soil_treatment_and_watering_rules.pdf",
      locator: "Page 2, Table 2, Row 4",
      similarity: 0.83,
      text: "[Source: soil_treatment_and_watering_rules.pdf : Page 2, Table 2, Row 4] rule_id: WTR-004 | temp_bracket_c: 20-25 | rainfall_bracket_mm: 0-10 | soil_type: sandy_loam | weekly_water_adjustment_mm: +5 | mulching_recommendation: 5cm organic pine bark or straw mulch to suppress evaporation under Cape south-easter winds.",
    },
  ],
  citations: [
    {
      source_file: "regional_soil_and_climate.csv",
      locator: "Row 1",
      label: "[regional_soil_and_climate.csv : Row 1]",
    },
    {
      source_file: "crop_planting_guide.json",
      locator: "Spinach",
      label: "[crop_planting_guide.json : Spinach]",
    },
    {
      source_file: "soil_treatment_and_watering_rules.pdf",
      locator: "Page 1, Table 1, Row 2",
      label: "[soil_treatment_and_watering_rules.pdf : Table 1, Row 2]",
    },
    {
      source_file: "soil_treatment_and_watering_rules.pdf",
      locator: "Page 2, Table 2, Row 4",
      label: "[soil_treatment_and_watering_rules.pdf : Table 2, Row 4]",
    },
  ],
};

export const INITIAL_AGENT_RESPONSE: AgentRunResponse = {
  run_id: "run_20261031_01",
  mode_used: "demo",
  summary: {
    raw_emails_count: 10,
    calendar_events_count: 8,
    merged_records_count: 8,
    verified_count: 3,
    auto_corrected_count: 2,
    flagged_count: 3,
  },
  workflow_nodes: [
    {
      node_id: "ingest_sources",
      step_number: 1,
      label: "1. Read Calendar & Emails",
      status: "completed",
      duration_ms: 42,
      summary_text: "Loaded 8 scheduled events & 10 raw gardener emails",
      input_payload: { events_count: 8, emails_count: 10 },
      output_payload: { raw_ingested_count: 18 },
    },
    {
      node_id: "clean_and_merge",
      step_number: 2,
      label: "2. Clean & Deduplicate Records",
      status: "completed",
      duration_ms: 58,
      summary_text: "Deduplicated 10 emails down to 8 canonical records",
      input_payload: { raw_emails_count: 10 },
      output_payload: { merged_records_count: 8, follow_ups_resolved: 2 },
    },
    {
      node_id: "validate_rules",
      step_number: 3,
      label: "3. Cross-Reference 3 Datasets",
      status: "completed",
      duration_ms: 85,
      summary_text: "Checked GBIF taxonomy, soil pH, and lime dosage",
      input_payload: { records_count: 8 },
      output_payload: {
        gbif_verified: 8,
        ph_checks_completed: 8,
        amendments_calculated: 8,
      },
    },
    {
      node_id: "fetch_weather",
      step_number: 4,
      label: "4. Live Forecast Check",
      status: "completed",
      duration_ms: 112,
      summary_text: "Queried Open-Meteo 7-day forecast for 6 suburbs",
      input_payload: { suburbs: ["Woodstock", "Khayelitsha", "Durbanville", "Bo-Kaap", "Mitchells Plain", "Rondebosch"] },
      output_payload: { forecasts_fetched: 6, frost_alerts: 0 },
    },
    {
      node_id: "flag_and_audit",
      step_number: 5,
      label: "5. Flag Discrepancies & Audit Log",
      status: "completed",
      duration_ms: 35,
      summary_text: "Flagged 3 out-of-range soil pH and 2 typos corrected",
      input_payload: { records_to_evaluate: 8 },
      output_payload: { verified: 3, auto_corrected: 2, flagged: 3 },
    },
  ],
  records: [
    {
      record_id: "REC-001",
      source_email_ids: ["EMAIL-101", "EMAIL-102"],
      raw_emails_before: [
        {
          email_id: "EMAIL-101",
          sender_name: "Sipho Ndlovu",
          sender_email: "sipho@capegardens.org.za",
          received_at: "2026-10-30T08:14:00Z",
          subject: "Woodstock plot planting update",
          body: "Good morning team, I have planted 24 Heirloom Tomatoes at plot PLOT-W04 today. Scientific name Solanumm lykopersikun. Forgot to take soil test, will send later.",
        },
        {
          email_id: "EMAIL-102",
          sender_name: "Sipho Ndlovu",
          sender_email: "sipho@capegardens.org.za",
          received_at: "2026-10-30T10:45:00Z",
          subject: "Re: Woodstock plot planting update",
          body: "Follow up: tested the soil pH at PLOT-W04 with the handheld probe and it came out to 5.3. Seed batch is BATCH-CT-2026-09.",
        },
      ],
      merge_audit_log: [
        "Merged follow-up EMAIL-102 into EMAIL-101 by sender_email and plot_id.",
        "Populated measured_soil_ph=5.3 from follow-up email.",
        "Populated seed_batch_id=BATCH-CT-2026-09 from follow-up email.",
      ],
      gardener_name: "Sipho Ndlovu",
      gardener_email: "sipho@capegardens.org.za",
      suburb: "Woodstock",
      soil_type: "sandy_loam",
      plot_id: "PLOT-W04",
      planted_date: "2026-11-02",
      crop_name: "Heirloom Tomato",
      species_scientific_raw: "Solanumm lykopersikun",
      species_scientific_verified: "Solanum lycopersicum",
      gbif_match_confidence: 96,
      quantity_planted: 24,
      measured_soil_ph: 5.3,
      ideal_ph_range: "6.0 - 6.8",
      seed_batch_id: "BATCH-CT-2026-09",
      soil_treatment_recommendation:
        "Apply 150g/m2 Agricultural Lime (sandy_loam, pH 5.3 -> 6.2)",
      weather_advisory:
        "21.4°C, 0mm rain, no frost risk in Woodstock over next 7 days",
      status: "FLAGGED",
      flags: ["SPECIES_TYPO_CORRECTED", "SOIL_PH_OUT_OF_RANGE"],
    },
    {
      record_id: "REC-002",
      source_email_ids: ["EMAIL-103"],
      raw_emails_before: [
        {
          email_id: "EMAIL-103",
          sender_name: "Nomvula Khumalo",
          sender_email: "nomvula@capegardens.org.za",
          received_at: "2026-10-30T09:20:00Z",
          subject: "Khayelitsha bed 12 spinach",
          body: "Planted 60 spinach plants at PLOT-K12. Soil test measured pH 6.4. Batch BATCH-CT-2026-02.",
        },
      ],
      merge_audit_log: ["Single email record ingested."],
      gardener_name: "Nomvula Khumalo",
      gardener_email: "nomvula@capegardens.org.za",
      suburb: "Khayelitsha",
      soil_type: "sandy",
      plot_id: "PLOT-K12",
      planted_date: "2026-11-03",
      crop_name: "Spinach",
      species_scientific_raw: "Spinacia oleracea",
      species_scientific_verified: "Spinacia oleracea",
      gbif_match_confidence: 98,
      quantity_planted: 60,
      measured_soil_ph: 6.4,
      ideal_ph_range: "6.0 - 7.0",
      seed_batch_id: "BATCH-CT-2026-02",
      soil_treatment_recommendation:
        "No amendment required. Maintain 5cm straw mulch.",
      weather_advisory: "22.1°C, 0mm rain, coastal wind advisory",
      status: "VERIFIED",
      flags: [],
    },
    {
      record_id: "REC-003",
      source_email_ids: ["EMAIL-104"],
      raw_emails_before: [
        {
          email_id: "EMAIL-104",
          sender_name: "David Van Der Merwe",
          sender_email: "david@capegardens.org.za",
          received_at: "2026-10-30T11:10:00Z",
          subject: "Durbanville Carrots Plot D08",
          body: "Durbanville clay loam bed sown with 120 Daucus carota seeds at PLOT-D08. Measured pH is 7.4. Batch BATCH-CT-2026-14.",
        },
      ],
      merge_audit_log: ["Single email record ingested."],
      gardener_name: "David Van Der Merwe",
      gardener_email: "david@capegardens.org.za",
      suburb: "Durbanville",
      soil_type: "clay_loam",
      plot_id: "PLOT-D08",
      planted_date: "2026-11-04",
      crop_name: "Carrot",
      species_scientific_raw: "Daucus carota",
      species_scientific_verified: "Daucus carota",
      gbif_match_confidence: 99,
      quantity_planted: 120,
      measured_soil_ph: 7.4,
      ideal_ph_range: "5.8 - 6.8",
      seed_batch_id: "BATCH-CT-2026-14",
      soil_treatment_recommendation:
        "Apply 90g/m2 Elemental Sulfur (clay_loam, pH 7.4 -> 6.6)",
      weather_advisory: "20.8°C, 0mm rain, low wind",
      status: "FLAGGED",
      flags: ["SOIL_PH_OUT_OF_RANGE"],
    },
    {
      record_id: "REC-004",
      source_email_ids: ["EMAIL-105"],
      raw_emails_before: [
        {
          email_id: "EMAIL-105",
          sender_name: "Fatima Patel",
          sender_email: "fatima@capegardens.org.za",
          received_at: "2026-10-30T12:00:00Z",
          subject: "Bo-Kaap peppers in ground",
          body: "Planted 18 Sweet Bell Pepper seedlings (Kapsikum anuum) at PLOT-BK02. Tested soil pH is 6.2. Batch BATCH-CT-2026-05.",
        },
      ],
      merge_audit_log: [
        "Single email record ingested.",
        "GBIF matched typo Kapsikum anuum to Capsicum annuum.",
      ],
      gardener_name: "Fatima Patel",
      gardener_email: "fatima@capegardens.org.za",
      suburb: "Bo-Kaap",
      soil_type: "loam",
      plot_id: "PLOT-BK02",
      planted_date: "2026-11-05",
      crop_name: "Sweet Bell Pepper",
      species_scientific_raw: "Kapsikum anuum",
      species_scientific_verified: "Capsicum annuum",
      gbif_match_confidence: 95,
      quantity_planted: 18,
      measured_soil_ph: 6.2,
      ideal_ph_range: "6.0 - 6.8",
      seed_batch_id: "BATCH-CT-2026-05",
      soil_treatment_recommendation:
        "Soil pH optimal. Incorporate compost before planting.",
      weather_advisory: "21.0°C, 0mm rain, sunny",
      status: "AUTO_CORRECTED",
      flags: ["SPECIES_TYPO_CORRECTED"],
    },
    {
      record_id: "REC-005",
      source_email_ids: ["EMAIL-106"],
      raw_emails_before: [
        {
          email_id: "EMAIL-106",
          sender_name: "Thabo Mthembu",
          sender_email: "thabo@capegardens.org.za",
          received_at: "2026-10-30T13:30:00Z",
          subject: "Mitchells Plain Beetroot",
          body: "45 beetroot sown in sandy plot PLOT-MP07 today. Soil pH 6.6. Batch BATCH-CT-2026-11.",
        },
      ],
      merge_audit_log: ["Single email record ingested."],
      gardener_name: "Thabo Mthembu",
      gardener_email: "thabo@capegardens.org.za",
      suburb: "Mitchells Plain",
      soil_type: "sandy",
      plot_id: "PLOT-MP07",
      planted_date: "2026-11-06",
      crop_name: "Beetroot",
      species_scientific_raw: "Beta vulgaris",
      species_scientific_verified: "Beta vulgaris",
      gbif_match_confidence: 97,
      quantity_planted: 45,
      measured_soil_ph: 6.6,
      ideal_ph_range: "6.2 - 7.0",
      seed_batch_id: "BATCH-CT-2026-11",
      soil_treatment_recommendation:
        "Soil pH in ideal range. Apply light mulch to conserve sandy moisture.",
      weather_advisory: "22.5°C, 0mm rain, mild breeze",
      status: "VERIFIED",
      flags: [],
    },
    {
      record_id: "REC-006",
      source_email_ids: ["EMAIL-107"],
      raw_emails_before: [
        {
          email_id: "EMAIL-107",
          sender_name: "Anika Botha",
          sender_email: "anika@capegardens.org.za",
          received_at: "2026-10-30T14:15:00Z",
          subject: "Rondebosch Bush Beans planted",
          body: "Completed planting 36 bush beans at PLOT-R15. Measured soil pH is 5.4. Batch BATCH-CT-2026-08.",
        },
      ],
      merge_audit_log: ["Single email record ingested."],
      gardener_name: "Anika Botha",
      gardener_email: "anika@capegardens.org.za",
      suburb: "Rondebosch",
      soil_type: "loam",
      plot_id: "PLOT-R15",
      planted_date: "2026-11-07",
      crop_name: "Bush Bean",
      species_scientific_raw: "Phaseolus vulgaris",
      species_scientific_verified: "Phaseolus vulgaris",
      gbif_match_confidence: 98,
      quantity_planted: 36,
      measured_soil_ph: 5.4,
      ideal_ph_range: "6.0 - 6.8",
      seed_batch_id: "BATCH-CT-2026-08",
      soil_treatment_recommendation:
        "Apply 110g/m2 Agricultural Lime (loam, pH 5.4 -> 6.3)",
      weather_advisory: "20.2°C, 0mm rain, shaded morning",
      status: "FLAGGED",
      flags: ["SOIL_PH_OUT_OF_RANGE"],
    },
    {
      record_id: "REC-007",
      source_email_ids: ["EMAIL-108"],
      raw_emails_before: [
        {
          email_id: "EMAIL-108",
          sender_name: "Lungile Jacobs",
          sender_email: "lungile@capegardens.org.za",
          received_at: "2026-10-30T15:00:00Z",
          subject: "Malmesbury Chard Planting",
          body: "50 Swiss Chard planted at PLOT-M03. Tested pH 6.3. Seed batch BATCH-CT-2026-03.",
        },
      ],
      merge_audit_log: ["Single email record ingested."],
      gardener_name: "Lungile Jacobs",
      gardener_email: "lungile@capegardens.org.za",
      suburb: "Malmesbury",
      soil_type: "clay",
      plot_id: "PLOT-M03",
      planted_date: "2026-11-08",
      crop_name: "Swiss Chard",
      species_scientific_raw: "Beta vulgaris subsp. vulgaris",
      species_scientific_verified: "Beta vulgaris subsp. vulgaris",
      gbif_match_confidence: 94,
      quantity_planted: 50,
      measured_soil_ph: 6.3,
      ideal_ph_range: "6.0 - 7.0",
      seed_batch_id: "BATCH-CT-2026-03",
      soil_treatment_recommendation:
        "Soil pH optimal. High organic matter recommended.",
      weather_advisory: "21.8°C, 0mm rain, calm",
      status: "VERIFIED",
      flags: [],
    },
    {
      record_id: "REC-008",
      source_email_ids: ["EMAIL-109", "EMAIL-110"],
      raw_emails_before: [
        {
          email_id: "EMAIL-109",
          sender_name: "Pieter De Villiers",
          sender_email: "pieter@capegardens.org.za",
          received_at: "2026-10-30T16:00:00Z",
          subject: "Constantia Kale planting",
          body: "Started planting about thirty kale plants (Brasika oleracia) at PLOT-C09. Will confirm exact count.",
        },
        {
          email_id: "EMAIL-110",
          sender_name: "Pieter De Villiers",
          sender_email: "pieter@capegardens.org.za",
          received_at: "2026-10-30T17:15:00Z",
          subject: "Re: Constantia Kale planting",
          body: "Exact count is 30 plants. Soil pH is 6.1. Seed batch BATCH-CT-2026-12.",
        },
      ],
      merge_audit_log: [
        "Merged follow-up EMAIL-110 into EMAIL-109 by sender_email and plot_id.",
        "Resolved ambiguous count 'about thirty' to exact quantity_planted=30.",
        "Populated measured_soil_ph=6.1 and seed_batch_id=BATCH-CT-2026-12.",
      ],
      gardener_name: "Pieter De Villiers",
      gardener_email: "pieter@capegardens.org.za",
      suburb: "Constantia",
      soil_type: "loam",
      plot_id: "PLOT-C09",
      planted_date: "2026-11-09",
      crop_name: "Kale",
      species_scientific_raw: "Brasika oleracia",
      species_scientific_verified: "Brassica oleracea",
      gbif_match_confidence: 99,
      quantity_planted: 30,
      measured_soil_ph: 6.1,
      ideal_ph_range: "6.0 - 7.5",
      seed_batch_id: "BATCH-CT-2026-12",
      soil_treatment_recommendation:
        "Soil pH balanced. Regular nitrogen feeding recommended.",
      weather_advisory: "19.5°C, 0mm rain, microclimate valley",
      status: "AUTO_CORRECTED",
      flags: ["QUANTITY_ROUNDED_FROM_FOLLOWUP", "SPECIES_TYPO_CORRECTED"],
    },
  ],
  csv_export:
    "record_id,gardener_name,suburb,plot_id,planted_date,crop_name,species_scientific_verified,quantity_planted,measured_soil_ph,seed_batch_id,status,flags\n" +
    "REC-001,Sipho Ndlovu,Woodstock,PLOT-W04,2026-11-02,Heirloom Tomato,Solanum lycopersicum,24,5.3,BATCH-CT-2026-09,FLAGGED,SPECIES_TYPO_CORRECTED;SOIL_PH_OUT_OF_RANGE\n" +
    "REC-002,Nomvula Khumalo,Khayelitsha,PLOT-K12,2026-11-03,Spinach,Spinacia oleracea,60,6.4,BATCH-CT-2026-02,VERIFIED,\n" +
    "REC-003,David Van Der Merwe,Durbanville,PLOT-D08,2026-11-04,Carrot,Daucus carota,120,7.4,BATCH-CT-2026-14,FLAGGED,SOIL_PH_OUT_OF_RANGE\n" +
    "REC-004,Fatima Patel,Bo-Kaap,PLOT-BK02,2026-11-05,Sweet Bell Pepper,Capsicum annuum,18,6.2,BATCH-CT-2026-05,AUTO_CORRECTED,SPECIES_TYPO_CORRECTED\n" +
    "REC-005,Thabo Mthembu,Mitchells Plain,PLOT-MP07,2026-11-06,Beetroot,Beta vulgaris,45,6.6,BATCH-CT-2026-11,VERIFIED,\n" +
    "REC-006,Anika Botha,Rondebosch,PLOT-R15,2026-11-07,Bush Bean,Phaseolus vulgaris,36,5.4,BATCH-CT-2026-08,FLAGGED,SOIL_PH_OUT_OF_RANGE\n" +
    "REC-007,Lungile Jacobs,Malmesbury,PLOT-M03,2026-11-08,Swiss Chard,Beta vulgaris subsp. vulgaris,50,6.3,BATCH-CT-2026-03,VERIFIED,\n" +
    "REC-008,Pieter De Villiers,Constantia,PLOT-C09,2026-11-09,Kale,Brassica oleracea,30,6.1,BATCH-CT-2026-12,AUTO_CORRECTED,QUANTITY_ROUNDED_FROM_FOLLOWUP\n",
};

export async function queryRagApi(
  question: string,
  chatHistory: ChatMessage[] = []
): Promise<RagQueryResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/rag/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        chat_history: chatHistory,
      }),
    });

    if (!res.ok) {
      throw new Error(`RAG API returned status ${res.status}`);
    }

    return (await res.json()) as RagQueryResponse;
  } catch (err) {
    console.warn("Backend unavailable, using initial RAG fixture:", err);
    return INITIAL_RAG_RESPONSE;
  }
}

export async function runVerificationAgentApi(
  mode: "demo" | "google_oauth" = "demo"
): Promise<AgentRunResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/agent/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ mode }),
    });

    if (!res.ok) {
      throw new Error(`Agent API returned status ${res.status}`);
    }

    return (await res.json()) as AgentRunResponse;
  } catch (err) {
    console.warn("Backend unavailable, using initial agent fixture:", err);
    return INITIAL_AGENT_RESPONSE;
  }
}

export async function fetchDataSourcesApi(): Promise<DataSourcesResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/data/sources`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!res.ok) {
      throw new Error(`Data sources API returned status ${res.status}`);
    }

    return (await res.json()) as DataSourcesResponse;
  } catch (err) {
    console.warn("Backend unavailable, using fallback data sources:", err);
    return {
      crops_json: [],
      suburbs_csv: [],
      pdf_tables: {
        table_1_soil_treatment: [],
        table_2_watering_rules: [],
      },
      demo_calendar_events: [],
      demo_gardener_emails: INITIAL_AGENT_RESPONSE.records.flatMap(
        (r) => r.raw_emails_before
      ),
      technical_summary_md:
        "# South African Gardener Guide - Technical Summary\n\nPreview mode fallback.",
    };
  }
}
