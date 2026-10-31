"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  CalendarEvent,
  DataSourcesResponse,
  RawEmailMessage,
  fetchDataSourcesApi,
} from "@/lib/api";
import { SourceFocus } from "@/lib/sourceLinks";

const HIGHLIGHT_ROW_CLASS = "bg-mint/70 ring-2 ring-inset ring-forest";

function SearchIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 text-forest flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function TableIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="18" height="18" x="3" y="3" rx="2" />
      <path d="M3 9h18" />
      <path d="M3 15h18" />
      <path d="M9 3v18" />
    </svg>
  );
}

function CalendarIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="18" height="18" x="3" y="4" rx="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}

function MailIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="20" height="16" x="2" y="4" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

interface CropItem {
  crop_name?: string;
  scientific_name?: string;
  category?: string;
  family?: string;
  optimal_ph_min?: number;
  optimal_ph_max?: number;
  soil_ph_min?: number;
  soil_ph_max?: number;
  water_mm_per_week?: number;
  frost_tolerance?: string;
  frost_tolerant?: boolean;
  companion_crops?: string;
  companion_plants?: string[] | string;
}

interface SuburbItem {
  suburb?: string;
  province?: string;
  soil_type?: string;
  baseline_ph_range?: string;
  baseline_ph_min?: number;
  baseline_ph_max?: number;
  summer_rain_mm?: number;
  winter_rain_mm?: number;
  annual_rainfall_mm?: number;
  frost_risk?: string;
  microclimate_notes?: string;
  typical_amendment_need?: string;
}

// Built-in Fallback Previews for when Backend is Offline
const FALLBACK_CROPS: CropItem[] = [
  {
    crop_name: "Spinach",
    scientific_name: "Spinacia oleracea",
    category: "Leafy Green",
    optimal_ph_min: 6.0,
    optimal_ph_max: 7.0,
    water_mm_per_week: 30,
    frost_tolerance: "Tolerant",
    companion_crops: "Strawberry, Cabbage, Cauliflower, Radish",
  },
  {
    crop_name: "Heirloom Tomato",
    scientific_name: "Solanum lycopersicum",
    category: "Fruiting",
    optimal_ph_min: 6.0,
    optimal_ph_max: 6.8,
    water_mm_per_week: 35,
    frost_tolerance: "Sensitive",
    companion_crops: "Basil, Marigold, Carrot, Onion",
  },
  {
    crop_name: "Carrot",
    scientific_name: "Daucus carota",
    category: "Root",
    optimal_ph_min: 6.0,
    optimal_ph_max: 6.8,
    water_mm_per_week: 25,
    frost_tolerance: "Tolerant",
    companion_crops: "Rosemary, Sage, Lettuce, Chives",
  },
  {
    crop_name: "Sweet Bell Pepper",
    scientific_name: "Capsicum annuum",
    category: "Fruiting",
    optimal_ph_min: 6.0,
    optimal_ph_max: 6.8,
    water_mm_per_week: 35,
    frost_tolerance: "Sensitive",
    companion_crops: "Basil, Parsley, Carrots, Onions",
  },
  {
    crop_name: "Beetroot",
    scientific_name: "Beta vulgaris",
    category: "Root",
    optimal_ph_min: 6.0,
    optimal_ph_max: 7.0,
    water_mm_per_week: 30,
    frost_tolerance: "Tolerant",
    companion_crops: "Bush Beans, Onions, Lettuce, Cabbage",
  },
  {
    crop_name: "Bush Bean",
    scientific_name: "Phaseolus vulgaris",
    category: "Legume",
    optimal_ph_min: 6.0,
    optimal_ph_max: 7.0,
    water_mm_per_week: 25,
    frost_tolerance: "Sensitive",
    companion_crops: "Cucumber, Corn, Strawberry, Celery",
  },
  {
    crop_name: "Swiss Chard",
    scientific_name: "Beta vulgaris subsp. vulgaris",
    category: "Leafy Green",
    optimal_ph_min: 6.0,
    optimal_ph_max: 7.0,
    water_mm_per_week: 30,
    frost_tolerance: "Tolerant",
    companion_crops: "Onion, Beetroot, Lavender, Thyme",
  },
  {
    crop_name: "Kale",
    scientific_name: "Brassica oleracea",
    category: "Leafy Green",
    optimal_ph_min: 6.0,
    optimal_ph_max: 7.5,
    water_mm_per_week: 30,
    frost_tolerance: "Tolerant",
    companion_crops: "Dill, Sage, Rosemary, Mint",
  },
  {
    crop_name: "Potato",
    scientific_name: "Solanum tuberosum",
    category: "Tuber",
    optimal_ph_min: 5.0,
    optimal_ph_max: 6.0,
    water_mm_per_week: 25,
    frost_tolerance: "Sensitive",
    companion_crops: "Horseradish, Marigold, Beans, Corn",
  },
  {
    crop_name: "Lettuce",
    scientific_name: "Lactuca sativa",
    category: "Leafy Green",
    optimal_ph_min: 6.0,
    optimal_ph_max: 7.0,
    water_mm_per_week: 25,
    frost_tolerance: "Tolerant",
    companion_crops: "Chives, Garlic, Radish, Carrots",
  },
  {
    crop_name: "Cabbage",
    scientific_name: "Brassica oleracea var. capitata",
    category: "Brassica",
    optimal_ph_min: 6.5,
    optimal_ph_max: 7.5,
    water_mm_per_week: 35,
    frost_tolerance: "Tolerant",
    companion_crops: "Sage, Thyme, Mint, Onions",
  },
  {
    crop_name: "Onion",
    scientific_name: "Allium cepa",
    category: "Allium",
    optimal_ph_min: 6.0,
    optimal_ph_max: 7.0,
    water_mm_per_week: 25,
    frost_tolerance: "Tolerant",
    companion_crops: "Carrot, Beetroot, Lettuce, Tomato",
  },
];

const FALLBACK_SUBURBS: SuburbItem[] = [
  {
    suburb: "Woodstock",
    province: "Western Cape",
    soil_type: "sandy_loam",
    baseline_ph_min: 5.3,
    baseline_ph_max: 5.8,
    summer_rain_mm: 18,
    winter_rain_mm: 82,
    frost_risk: "None",
    microclimate_notes: "Well-draining urban coastal slope prone to summer drying winds.",
  },
  {
    suburb: "Constantia",
    province: "Western Cape",
    soil_type: "loam",
    baseline_ph_min: 5.8,
    baseline_ph_max: 6.5,
    summer_rain_mm: 25,
    winter_rain_mm: 110,
    frost_risk: "None",
    microclimate_notes: "Deep rich valley soil with high organic matter and reliable moisture.",
  },
  {
    suburb: "Kirstenbosch",
    province: "Western Cape",
    soil_type: "loam",
    baseline_ph_min: 5.7,
    baseline_ph_max: 6.4,
    summer_rain_mm: 30,
    winter_rain_mm: 130,
    frost_risk: "None",
    microclimate_notes: "High rainfall mountain microclimate with fertile decomposed granite.",
  },
  {
    suburb: "Bellville",
    province: "Western Cape",
    soil_type: "clay_loam",
    baseline_ph_min: 6.0,
    baseline_ph_max: 6.8,
    summer_rain_mm: 14,
    winter_rain_mm: 70,
    frost_risk: "Low",
    microclimate_notes: "Warm northern suburbs plain with heavier clay loam moisture retention.",
  },
  {
    suburb: "Durbanville",
    province: "Western Cape",
    soil_type: "clay_loam",
    baseline_ph_min: 6.1,
    baseline_ph_max: 6.9,
    summer_rain_mm: 16,
    winter_rain_mm: 75,
    frost_risk: "Low",
    microclimate_notes: "Rolling hill topography with fertile wine country soils and alkaline pockets.",
  },
  {
    suburb: "Observatory",
    province: "Western Cape",
    soil_type: "clay",
    baseline_ph_min: 5.9,
    baseline_ph_max: 6.6,
    summer_rain_mm: 18,
    winter_rain_mm: 80,
    frost_risk: "None",
    microclimate_notes: "Liesberg floodplain clay requiring compost aeration for vegetable roots.",
  },
  {
    suburb: "Hout Bay",
    province: "Western Cape",
    soil_type: "sandy_loam",
    baseline_ph_min: 5.5,
    baseline_ph_max: 6.2,
    summer_rain_mm: 22,
    winter_rain_mm: 95,
    frost_risk: "None",
    microclimate_notes: "Coastal valley protected from north-westers but exposed to sea breezes.",
  },
  {
    suburb: "Khayelitsha",
    province: "Western Cape",
    soil_type: "clay",
    baseline_ph_min: 5.9,
    baseline_ph_max: 6.7,
    summer_rain_mm: 15,
    winter_rain_mm: 68,
    frost_risk: "None",
    microclimate_notes: "Cape Flats coastal lowland with heavy marine clay requiring sandy amendments.",
  },
  {
    suburb: "Mitchells Plain",
    province: "Western Cape",
    soil_type: "sandy",
    baseline_ph_min: 6.5,
    baseline_ph_max: 7.2,
    summer_rain_mm: 14,
    winter_rain_mm: 65,
    frost_risk: "None",
    microclimate_notes: "Alkaline calcitic coastal sand dunes requiring heavy mulching to retain water.",
  },
  {
    suburb: "Rondebosch",
    province: "Western Cape",
    soil_type: "loam",
    baseline_ph_min: 5.8,
    baseline_ph_max: 6.5,
    summer_rain_mm: 22,
    winter_rain_mm: 105,
    frost_risk: "None",
    microclimate_notes: "Southern suburbs shaded canopy with naturally balanced pH and good humus.",
  },
];

const FALLBACK_TABLE_1_RULES = [
  { rule_id: "RULE-PH-01", soil_type: "sandy", current_ph_bracket: "5.0 - 5.5", target_ph_shift: "+1.0", amendment_type: "Agricultural Lime", dosage_g_per_m2: "100", application_notes: "Incorporate 100g/m2 calcitic lime into top 15cm of sandy soil 2 weeks before planting" },
  { rule_id: "RULE-PH-02", soil_type: "sandy_loam", current_ph_bracket: "5.0 - 5.5", target_ph_shift: "+0.9", amendment_type: "Agricultural Lime", dosage_g_per_m2: "150", application_notes: "Work into top 15cm soil 2-3 weeks prior to planting; water deeply" },
  { rule_id: "RULE-PH-03", soil_type: "loam", current_ph_bracket: "5.0 - 5.5", target_ph_shift: "+0.8", amendment_type: "Agricultural Lime", dosage_g_per_m2: "200", application_notes: "Apply 200g/m2 lime evenly, hoe into top 20cm soil, allow 3 weeks" },
  { rule_id: "RULE-PH-04", soil_type: "clay_loam", current_ph_bracket: "5.0 - 5.5", target_ph_shift: "+0.7", amendment_type: "Agricultural Lime", dosage_g_per_m2: "250", application_notes: "Heavier soils require 250g/m2 lime plus gypsum to maintain crumb structure" },
  { rule_id: "RULE-PH-05", soil_type: "clay", current_ph_bracket: "5.0 - 5.5", target_ph_shift: "+0.6", amendment_type: "Agricultural Lime", dosage_g_per_m2: "300", application_notes: "Heavy clay buffering: 300g/m2 lime worked in 4 weeks ahead of planting" },
  { rule_id: "RULE-PH-06", soil_type: "sandy", current_ph_bracket: "4.5 - 5.0", target_ph_shift: "+1.5", amendment_type: "Dolomitic Lime", dosage_g_per_m2: "180", application_notes: "Severe acidity: apply dolomitic lime to supply magnesium and calcium" },
  { rule_id: "RULE-PH-07", soil_type: "sandy_loam", current_ph_bracket: "4.5 - 5.0", target_ph_shift: "+1.3", amendment_type: "Dolomitic Lime", dosage_g_per_m2: "220", application_notes: "Split application: 120g/m2 first week, 100g/m2 two weeks later" },
  { rule_id: "RULE-PH-08", soil_type: "loam", current_ph_bracket: "4.5 - 5.0", target_ph_shift: "+1.2", amendment_type: "Agricultural Lime", dosage_g_per_m2: "280", application_notes: "Deep rototill lime into root zone with organic compost" },
  { rule_id: "RULE-PH-09", soil_type: "clay_loam", current_ph_bracket: "4.5 - 5.0", target_ph_shift: "+1.0", amendment_type: "Agricultural Lime", dosage_g_per_m2: "340", application_notes: "Apply 340g/m2 in autumn for spring planting beds" },
  { rule_id: "RULE-PH-10", soil_type: "clay", current_ph_bracket: "4.5 - 5.0", target_ph_shift: "+0.9", amendment_type: "Agricultural Lime", dosage_g_per_m2: "400", application_notes: "Maximum single application limit: 400g/m2. Retest after 6 weeks" },
  { rule_id: "RULE-PH-11", soil_type: "sandy", current_ph_bracket: "5.5 - 6.0", target_ph_shift: "+0.6", amendment_type: "Agricultural Lime", dosage_g_per_m2: "70", application_notes: "Light maintenance dusting of calcitic lime before planting" },
  { rule_id: "RULE-PH-12", soil_type: "sandy_loam", current_ph_bracket: "5.5 - 6.0", target_ph_shift: "+0.5", amendment_type: "Agricultural Lime", dosage_g_per_m2: "90", application_notes: "Work 90g/m2 into top 10cm before planting brassicas or alliums" },
  { rule_id: "RULE-PH-13", soil_type: "loam", current_ph_bracket: "5.5 - 6.0", target_ph_shift: "+0.5", amendment_type: "Agricultural Lime", dosage_g_per_m2: "120", application_notes: "Apply 120g/m2 alongside well-rotted kraal manure" },
  { rule_id: "RULE-PH-14", soil_type: "clay_loam", current_ph_bracket: "5.5 - 6.0", target_ph_shift: "+0.4", amendment_type: "Agricultural Lime", dosage_g_per_m2: "150", application_notes: "Standard pre-planting liming for neutral-loving crops" },
  { rule_id: "RULE-PH-15", soil_type: "clay", current_ph_bracket: "5.5 - 6.0", target_ph_shift: "+0.4", amendment_type: "Agricultural Lime", dosage_g_per_m2: "180", application_notes: "Apply 180g/m2 and mulch with rooibos tea compost" },
  { rule_id: "RULE-PH-16", soil_type: "sandy", current_ph_bracket: "7.2 - 7.8", target_ph_shift: "-0.6", amendment_type: "Elemental Sulfur", dosage_g_per_m2: "50", application_notes: "Coastal calcitic dunes: apply sulfur powder 4 weeks prior to planting" },
  { rule_id: "RULE-PH-17", soil_type: "sandy_loam", current_ph_bracket: "7.2 - 7.8", target_ph_shift: "-0.5", amendment_type: "Elemental Sulfur", dosage_g_per_m2: "75", application_notes: "Work sulfur into moist soil; soil microbes require warmth to oxidize" },
  { rule_id: "RULE-PH-18", soil_type: "loam", current_ph_bracket: "7.2 - 7.8", target_ph_shift: "-0.5", amendment_type: "Elemental Sulfur", dosage_g_per_m2: "100", application_notes: "Apply 100g/m2 sulfur with acid compost (pine needle or oak leaf)" },
  { rule_id: "RULE-PH-19", soil_type: "clay_loam", current_ph_bracket: "7.2 - 7.8", target_ph_shift: "-0.4", amendment_type: "Elemental Sulfur", dosage_g_per_m2: "130", application_notes: "Acidify clay loam gradually; retest pH before tuber crops" },
  { rule_id: "RULE-PH-20", soil_type: "clay", current_ph_bracket: "7.2 - 7.8", target_ph_shift: "-0.4", amendment_type: "Elemental Sulfur", dosage_g_per_m2: "160", application_notes: "Work 160g/m2 sulfur into top 15cm; avoid root contact with seedlings" },
  { rule_id: "RULE-PH-21", soil_type: "sandy", current_ph_bracket: "7.8 - 8.5", target_ph_shift: "-1.0", amendment_type: "Elemental Sulfur", dosage_g_per_m2: "100", application_notes: "Heavy alkaline sand: split sulfur dose over two months" },
  { rule_id: "RULE-PH-22", soil_type: "sandy_loam", current_ph_bracket: "7.8 - 8.5", target_ph_shift: "-0.9", amendment_type: "Elemental Sulfur", dosage_g_per_m2: "140", application_notes: "Incorporate sulfur plus iron chelate to prevent chlorosis" },
  { rule_id: "RULE-PH-23", soil_type: "loam", current_ph_bracket: "7.8 - 8.5", target_ph_shift: "-0.8", amendment_type: "Elemental Sulfur", dosage_g_per_m2: "180", application_notes: "Combine 180g/m2 sulfur with generous pine bark mulching" },
  { rule_id: "RULE-PH-24", soil_type: "clay_loam", current_ph_bracket: "7.8 - 8.5", target_ph_shift: "-0.7", amendment_type: "Elemental Sulfur", dosage_g_per_m2: "220", application_notes: "Broadcast 220g/m2 sulfur in early autumn before winter rains" },
  { rule_id: "RULE-PH-25", soil_type: "clay", current_ph_bracket: "7.8 - 8.5", target_ph_shift: "-0.6", amendment_type: "Elemental Sulfur", dosage_g_per_m2: "260", application_notes: "Maximum safe sulfur rate for heavy clay; monitor soil EC" },
];

const FALLBACK_TABLE_2_RULES = [
  { rule_id: "RULE-WT-01", temp_bracket_c: "< 20", rainfall_bracket_mm: "> 40", soil_type: "sandy", weekly_water_adjustment_mm: "-15", mulching_recommendation: "Light bark mulch 2cm to prevent crusting" },
  { rule_id: "RULE-WT-02", temp_bracket_c: "< 20", rainfall_bracket_mm: "20-40", soil_type: "sandy_loam", weekly_water_adjustment_mm: "-10", mulching_recommendation: "3cm organic straw mulch" },
  { rule_id: "RULE-WT-03", temp_bracket_c: "< 20", rainfall_bracket_mm: "0-20", soil_type: "loam", weekly_water_adjustment_mm: "0", mulching_recommendation: "4cm compost mulch" },
  { rule_id: "RULE-WT-04", temp_bracket_c: "20-25", rainfall_bracket_mm: "0-10", soil_type: "sandy_loam", weekly_water_adjustment_mm: "+5", mulching_recommendation: "5cm organic pine bark or straw mulch to suppress evaporation under Cape south-easter winds" },
  { rule_id: "RULE-WT-05", temp_bracket_c: "20-25", rainfall_bracket_mm: "10-25", soil_type: "clay_loam", weekly_water_adjustment_mm: "0", mulching_recommendation: "3cm coarse compost mulch" },
  { rule_id: "RULE-WT-06", temp_bracket_c: "20-25", rainfall_bracket_mm: "> 25", soil_type: "clay", weekly_water_adjustment_mm: "-10", mulching_recommendation: "Keep drainage clear, 2cm light leaf mulch" },
  { rule_id: "RULE-WT-07", temp_bracket_c: "25-30", rainfall_bracket_mm: "0-10", soil_type: "sandy", weekly_water_adjustment_mm: "+15", mulching_recommendation: "7cm dense straw mulch with shade cloth afternoon" },
  { rule_id: "RULE-WT-08", temp_bracket_c: "25-30", rainfall_bracket_mm: "0-10", soil_type: "sandy_loam", weekly_water_adjustment_mm: "+10", mulching_recommendation: "5cm pine bark mulch; water at dawn" },
  { rule_id: "RULE-WT-09", temp_bracket_c: "25-30", rainfall_bracket_mm: "10-25", soil_type: "loam", weekly_water_adjustment_mm: "+5", mulching_recommendation: "5cm compost mulch to maintain cool root zone" },
  { rule_id: "RULE-WT-10", temp_bracket_c: "25-30", rainfall_bracket_mm: "> 25", soil_type: "clay_loam", weekly_water_adjustment_mm: "0", mulching_recommendation: "3cm mulch; monitor for fungal issues" },
  { rule_id: "RULE-WT-11", temp_bracket_c: "> 30", rainfall_bracket_mm: "0-5", soil_type: "sandy", weekly_water_adjustment_mm: "+25", mulching_recommendation: "Double mulch (8cm) plus micro-drip irrigation" },
  { rule_id: "RULE-WT-12", temp_bracket_c: "> 30", rainfall_bracket_mm: "0-5", soil_type: "sandy_loam", weekly_water_adjustment_mm: "+20", mulching_recommendation: "6cm straw mulch, drip line beneath mulch" },
  { rule_id: "RULE-WT-13", temp_bracket_c: "> 30", rainfall_bracket_mm: "0-5", soil_type: "loam", weekly_water_adjustment_mm: "+15", mulching_recommendation: "6cm composted bark mulch; deep dawn soaking" },
  { rule_id: "RULE-WT-14", temp_bracket_c: "> 30", rainfall_bracket_mm: "0-5", soil_type: "clay_loam", weekly_water_adjustment_mm: "+10", mulching_recommendation: "5cm mulch to prevent surface cracking" },
  { rule_id: "RULE-WT-15", temp_bracket_c: "> 30", rainfall_bracket_mm: "0-5", soil_type: "clay", weekly_water_adjustment_mm: "+5", mulching_recommendation: "4cm mulch; avoid heavy pooling on clay" },
  { rule_id: "RULE-WT-16", temp_bracket_c: "15-20", rainfall_bracket_mm: "15-30", soil_type: "sandy", weekly_water_adjustment_mm: "-5", mulching_recommendation: "2cm gravel or fine bark mulch" },
  { rule_id: "RULE-WT-17", temp_bracket_c: "15-20", rainfall_bracket_mm: "15-30", soil_type: "sandy_loam", weekly_water_adjustment_mm: "-5", mulching_recommendation: "3cm straw mulch" },
  { rule_id: "RULE-WT-18", temp_bracket_c: "15-20", rainfall_bracket_mm: "30-50", soil_type: "loam", weekly_water_adjustment_mm: "-15", mulching_recommendation: "Minimal mulching to permit soil aeration" },
  { rule_id: "RULE-WT-19", temp_bracket_c: "15-20", rainfall_bracket_mm: "> 50", soil_type: "clay_loam", weekly_water_adjustment_mm: "-20", mulching_recommendation: "Ensure furrow drainage is clear" },
  { rule_id: "RULE-WT-20", temp_bracket_c: "15-20", rainfall_bracket_mm: "> 50", soil_type: "clay", weekly_water_adjustment_mm: "-25", mulching_recommendation: "Suspend irrigation; high root rot risk" },
];

const FALLBACK_CALENDAR: CalendarEvent[] = [
  { event_id: "EVT-01", scheduled_date: "2026-11-02", suburb: "Woodstock", plot_id: "PLOT-W04", gardener_name: "Sipho Ndlovu", gardener_email: "sipho@capegardens.org.za", notes: "Scheduled heirloom tomato bed planting after morning soil prep." },
  { event_id: "EVT-02", scheduled_date: "2026-11-03", suburb: "Khayelitsha", plot_id: "PLOT-K12", gardener_name: "Nomvula Khumalo", gardener_email: "nomvula@capegardens.org.za", notes: "Spinach bed installation in communal raised bed section." },
  { event_id: "EVT-03", scheduled_date: "2026-11-04", suburb: "Durbanville", plot_id: "PLOT-D08", gardener_name: "David Van Der Merwe", gardener_email: "david@capegardens.org.za", notes: "Daucus carota sowing in well-tilled clay loam bed." },
  { event_id: "EVT-04", scheduled_date: "2026-11-05", suburb: "Bo-Kaap", plot_id: "PLOT-BK02", gardener_name: "Fatima Patel", gardener_email: "fatima@capegardens.org.za", notes: "Sweet bell pepper seedling transplanting in sunny terrace plot." },
  { event_id: "EVT-05", scheduled_date: "2026-11-06", suburb: "Mitchells Plain", plot_id: "PLOT-MP07", gardener_name: "Thabo Mthembu", gardener_email: "thabo@capegardens.org.za", notes: "Direct seeding beetroot rows with drip line alignment." },
  { event_id: "EVT-06", scheduled_date: "2026-11-07", suburb: "Rondebosch", plot_id: "PLOT-R15", gardener_name: "Anika Botha", gardener_email: "anika@capegardens.org.za", notes: "Bush bean planting in partially shaded loam section." },
  { event_id: "EVT-07", scheduled_date: "2026-11-08", suburb: "Malmesbury", plot_id: "PLOT-M03", gardener_name: "Lungile Jacobs", gardener_email: "lungile@capegardens.org.za", notes: "Swiss chard bed planting with compost amendment." },
  { event_id: "EVT-08", scheduled_date: "2026-11-09", suburb: "Constantia", plot_id: "PLOT-C09", gardener_name: "Pieter De Villiers", gardener_email: "pieter@capegardens.org.za", notes: "Tuscan kale seedlings planting in raised terrace bed 9." },
];

const FALLBACK_EMAILS: RawEmailMessage[] = [
  { email_id: "EMAIL-101", sender_name: "Sipho Ndlovu", sender_email: "sipho@capegardens.org.za", received_at: "2026-10-30T08:14:00Z", subject: "Woodstock plot planting update", body: "Good morning team, I have planted 24 Heirloom Tomatoes at plot PLOT-W04 today. Scientific name Solanumm lykopersikun. Forgot to take soil test, will send later." },
  { email_id: "EMAIL-102", sender_name: "Sipho Ndlovu", sender_email: "sipho@capegardens.org.za", received_at: "2026-10-30T10:45:00Z", subject: "Re: Woodstock plot planting update", body: "Follow up: tested the soil pH at PLOT-W04 with the handheld probe and it came out to 5.3. Seed batch is BATCH-CT-2026-09." },
  { email_id: "EMAIL-103", sender_name: "Nomvula Khumalo", sender_email: "nomvula@capegardens.org.za", received_at: "2026-10-30T09:20:00Z", subject: "Khayelitsha bed 12 spinach", body: "Planted 60 spinach plants at PLOT-K12. Soil test measured pH 6.4. Batch BATCH-CT-2026-02." },
  { email_id: "EMAIL-104", sender_name: "David Van Der Merwe", sender_email: "david@capegardens.org.za", received_at: "2026-10-30T11:10:00Z", subject: "Durbanville Carrots Plot D08", body: "Durbanville clay loam bed sown with 120 Daucus carota seeds at PLOT-D08. Measured pH is 7.4. Batch BATCH-CT-2026-14." },
  { email_id: "EMAIL-105", sender_name: "Fatima Patel", sender_email: "fatima@capegardens.org.za", received_at: "2026-10-30T11:45:00Z", subject: "Bo-Kaap peppers PLOT-BK02", body: "Transplanted 18 sweet bell peppers (Kapsikum anuum) into terrace bed PLOT-BK02. Soil test pH is 6.2. Batch BATCH-CT-2026-05." },
  { email_id: "EMAIL-106", sender_name: "Thabo Mthembu", sender_email: "thabo@capegardens.org.za", received_at: "2026-10-30T13:05:00Z", subject: "Mitchells Plain Beetroot PLOT-MP07", body: "Planted 45 beetroot plants at PLOT-MP07. Tested sandy soil pH 6.6. Batch BATCH-CT-2026-11." },
  { email_id: "EMAIL-107", sender_name: "Anika Botha", sender_email: "anika@capegardens.org.za", received_at: "2026-10-30T14:15:00Z", subject: "Rondebosch Bush Beans", body: "Sowed 36 Phaseolus vulgaris bush beans at PLOT-R15. Tested soil pH 5.4. Batch BATCH-CT-2026-08." },
  { email_id: "EMAIL-108", sender_name: "Lungile Jacobs", sender_email: "lungile@capegardens.org.za", received_at: "2026-10-30T15:00:00Z", subject: "Malmesbury plot M03 Swiss Chard", body: "Completed planting 50 Swiss Chard at PLOT-M03. Handheld probe reads soil pH 6.3. Batch BATCH-CT-2026-03." },
  { email_id: "EMAIL-109", sender_name: "Pieter De Villiers", sender_email: "pieter@capegardens.org.za", received_at: "2026-10-30T15:30:00Z", subject: "Constantia Kale planting", body: "Planted about thirty kale seedlings (Brasika oleracia) at PLOT-C09. Will follow up with exact batch and soil test shortly." },
  { email_id: "EMAIL-110", sender_name: "Pieter De Villiers", sender_email: "pieter@capegardens.org.za", received_at: "2026-10-30T16:15:00Z", subject: "Re: Constantia Kale planting", body: "Exact count is 30 plants. Soil pH is 6.1. Seed batch BATCH-CT-2026-12." },
];

const FALLBACK_TECHNICAL_SUMMARY = `# South African Community Gardener Guide and Verification System
## Comprehensive Technical Summary & Architecture Specification

### 1. Architectural Mission
The Western Cape agricultural basin presents distinct microclimatic challenges: winter rainfall Mediterranean zones, intense summer drying winds (the Cape Doctor), and heterogeneous soil textures ranging from coastal sands (pH 6.5-7.2) to acidic slopes (pH 5.0-5.8). This system unifies agronomic knowledge retrieval and automated field planting verification across two tightly integrated subsystems.

### 2. Part 1: Structured Multi-Hop Agronomic RAG
* **Embedding Model**: BAAI/bge-small-en-v1.5 (384-dimensional dense semantic representations) running inside local ChromaDB vector storage.
* **Hybrid Retrieval Seam**: Combines dense vector similarity with structure-aware field matching for suburb baselines, crop requirements, and amendment rules.
* **Multi-Hop Query Decomposition**: User questions are automatically transformed into distinct sub-queries targeting CSV suburb baselines, JSON crop guides, and PDF amendment dosage tables.
* **Live Environmental Synthesis**: Real-time Open-Meteo 7-day temperature and precipitation observations ground the agronomic advice. Every assertion carries verifiable bracketed citations (e.g., [crop_planting_guide.json : Spinach]).

### 3. Part 2: Autonomous Planting Verification Agent
* **LangGraph 5-Step StateGraph Pipeline**:
  1. \`ingest_sources\`: Ingests scheduled calendar events and gardener email submissions.
  2. \`clean_and_merge\`: Deduplicates multiple follow-up emails per gardener and plot into canonical records.
  3. \`validate_rules\`: Cross-references species names against GBIF Taxonomic Species API, compares soil pH to crop tolerances, and looks up lime/sulfur dosages.
  4. \`fetch_weather\`: Verifies 7-day forecast for frost risk and moisture stress across Western Cape suburbs.
  5. \`flag_and_audit\`: Classifies records as VERIFIED, AUTO_CORRECTED, or FLAGGED with exhaustive audit logs and CSV export.

### 4. Verification Benchmark & Reliability Invariants
* 100% test pass rate across 10 deterministic test suites.
* Deduplication accurately maps 10 raw emails down to 8 canonical plot records.
* Typo auto-correction via GBIF corrects species scientific names (e.g., Solanumm lykopersikun to Solanum lycopersicum with 96% match confidence).
* Discrepancies are flagged without dropping data: out-of-range soil pH values trigger concrete dosage recommendations from municipal PDF tables.

### 5. Known Limitations and Practical Production Next Steps
1. **Live Google OAuth & Account Permissions**: The backend includes working Gmail and Google Calendar API adapters, but currently defaults to realistic fixture data. Live Google integration requires registering an approved Google Cloud OAuth Consent Screen and provisioning client refresh tokens. In production, we would complete Google's verification process so garden coordinators can sign in with their Google accounts with one click and ingest live field inboxes.
2. **Vector Store Concurrency & Scaling**: We chose embedded ChromaDB SQLite because it keeps local evaluation and single-container cloud hosting completely self-contained with zero external database dependencies. Because SQLite operates in single-writer mode, a busy production setup with dozens of simultaneous workers would benefit from migrating to PostgreSQL with \`pgvector\` or managed Qdrant.
3. **Real-Time Webhooks vs. On-Demand Runs**: Currently, the verification workflow runs on demand when triggered from the dashboard. In a live deployment, Google Cloud Pub/Sub push notifications (\`users.watch\` for Gmail) and Google Calendar push webhooks would verify incoming field emails automatically the moment they land in the inbox.
4. **Closing the Loop with SMS and WhatsApp Alerts**: When a plot is flagged for acidic soil or missing batch numbers, the agent calculates the exact lime dosage for manager review. The next step is adding direct messaging: an extension officer can approve the recommendation with one click and automatically text the treatment instructions straight to the gardener's phone via SMS or WhatsApp.`;

type SubTabKey = "crops" | "suburbs" | "pdf_tables" | "part2_demo" | "technical_summary";

interface DataExplorerProps {
  /** Record to open, scroll to, and highlight (set when a citation is clicked). */
  focusTarget?: SourceFocus | null;
  /** Returns to the Garden Guide answer that the citation came from. */
  onBackToAnswer?: () => void;
}

export function DataExplorer({ focusTarget = null, onBackToAnswer }: DataExplorerProps) {
  const [activeTab, setActiveTab] = useState<SubTabKey>("crops");
  const [dataSources, setDataSources] = useState<DataSourcesResponse | null>(null);
  const [cropSearch, setCropSearch] = useState<string>("");
  const [suburbSearch, setSuburbSearch] = useState<string>("");
  const [activePdfTable, setActivePdfTable] = useState<"table_1" | "table_2">("table_1");
  const [activeDemoSubTab, setActiveDemoSubTab] = useState<"calendar" | "emails">("calendar");

  // Progressive disclosure states so opening a sub-tab is calm and readable
  const [showAllCrops, setShowAllCrops] = useState<boolean>(false);
  const [showAllSuburbs, setShowAllSuburbs] = useState<boolean>(false);
  const [showAllPdfRules, setShowAllPdfRules] = useState<boolean>(false);
  const [expandedEmails, setExpandedEmails] = useState<Record<string, boolean>>({});
  const [expandedSections, setExpandedSections] = useState<Record<number, boolean>>({ 0: true });
  const [highlightKey, setHighlightKey] = useState<string | null>(null);

  // Step 1: when a citation is clicked, make sure the target row is rendered
  // (right sub-tab, right PDF table, no search filter, full list expanded).
  useEffect(() => {
    if (!focusTarget) {
      setHighlightKey(null);
      return;
    }
    setActiveTab(focusTarget.subTab);
    if (focusTarget.subTab === "crops" && focusTarget.cropName) {
      setCropSearch("");
      setShowAllCrops(true);
      setHighlightKey(`crop:${focusTarget.cropName.toLowerCase()}`);
    } else if (focusTarget.subTab === "suburbs" && focusTarget.rowIndex !== undefined) {
      setSuburbSearch("");
      setShowAllSuburbs(true);
      setHighlightKey(`suburb:${focusTarget.rowIndex}`);
    } else if (
      focusTarget.subTab === "pdf_tables" &&
      focusTarget.pdfTable &&
      focusTarget.rowIndex !== undefined
    ) {
      setActivePdfTable(focusTarget.pdfTable);
      setShowAllPdfRules(true);
      setHighlightKey(`${focusTarget.pdfTable}:${focusTarget.rowIndex}`);
    }
  }, [focusTarget]);

  // Step 2: after the row renders, scroll it to the centre of the viewport.
  // Re-runs when live API data replaces the fallback rows.
  useEffect(() => {
    if (!highlightKey) return;
    const timer = window.setTimeout(() => {
      const row = document.querySelector<HTMLElement>(
        `[data-source-row="${CSS.escape(highlightKey)}"]`
      );
      row?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 120);
    return () => window.clearTimeout(timer);
  }, [highlightKey, activeTab, activePdfTable, dataSources]);

  const scrollIntoFrame = (el: HTMLElement | null) => {
    if (!el) return;
    window.setTimeout(() => {
      const rect = el.getBoundingClientRect();
      if (rect.bottom > window.innerHeight - 24 || rect.top < 88) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }, 70);
  };

  useEffect(() => {
    let isMounted = true;
    fetchDataSourcesApi()
      .then((data) => {
        if (isMounted) {
          setDataSources(data);
        }
      })
      .catch((err) => {
        console.warn("Could not load backend data sources, using fallback:", err);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const cropsList: CropItem[] = useMemo(() => {
    const list = (dataSources?.crops_json && dataSources.crops_json.length > 0
      ? dataSources.crops_json
      : FALLBACK_CROPS) as CropItem[];

    return list.filter((crop) => {
      if (!cropSearch.trim()) return true;
      const term = cropSearch.toLowerCase();
      const name = String(crop.crop_name || "").toLowerCase();
      const sci = String(crop.scientific_name || "").toLowerCase();
      const comp = String(
        Array.isArray(crop.companion_plants)
          ? crop.companion_plants.join(" ")
          : crop.companion_crops || crop.companion_plants || ""
      ).toLowerCase();
      return name.includes(term) || sci.includes(term) || comp.includes(term);
    });
  }, [dataSources, cropSearch]);

  const suburbsList: SuburbItem[] = useMemo(() => {
    const list = (dataSources?.suburbs_csv && dataSources.suburbs_csv.length > 0
      ? dataSources.suburbs_csv
      : FALLBACK_SUBURBS) as SuburbItem[];

    return list.filter((sub) => {
      if (!suburbSearch.trim()) return true;
      const term = suburbSearch.toLowerCase();
      const name = String(sub.suburb || "").toLowerCase();
      const soil = String(sub.soil_type || "").toLowerCase();
      const prov = String(sub.province || "").toLowerCase();
      return name.includes(term) || soil.includes(term) || prov.includes(term);
    });
  }, [dataSources, suburbSearch]);

  const table1Rules = useMemo(() => {
    if (
      dataSources?.pdf_tables?.table_1_soil_treatment &&
      dataSources.pdf_tables.table_1_soil_treatment.length > 0
    ) {
      return dataSources.pdf_tables.table_1_soil_treatment;
    }
    return FALLBACK_TABLE_1_RULES;
  }, [dataSources]);

  const table2Rules = useMemo(() => {
    if (
      dataSources?.pdf_tables?.table_2_watering_rules &&
      dataSources.pdf_tables.table_2_watering_rules.length > 0
    ) {
      return dataSources.pdf_tables.table_2_watering_rules;
    }
    return FALLBACK_TABLE_2_RULES;
  }, [dataSources]);

  const calendarEvents = useMemo(() => {
    if (
      dataSources?.demo_calendar_events &&
      dataSources.demo_calendar_events.length > 0
    ) {
      return dataSources.demo_calendar_events;
    }
    return FALLBACK_CALENDAR;
  }, [dataSources]);

  const gardenerEmails = useMemo(() => {
    if (
      dataSources?.demo_gardener_emails &&
      dataSources.demo_gardener_emails.length > 0
    ) {
      return dataSources.demo_gardener_emails;
    }
    return FALLBACK_EMAILS;
  }, [dataSources]);

  const technicalSummaryText =
    dataSources?.technical_summary_md &&
    dataSources.technical_summary_md.trim().length > 100
      ? dataSources.technical_summary_md
      : FALLBACK_TECHNICAL_SUMMARY;

  const summarySections = useMemo(() => {
    const rawParts = technicalSummaryText.split(/\n(?=##\s+)/);
    return rawParts
      .map((part, idx) => {
        const lines = part.trim().split("\n");
        const firstLine = lines[0]?.replace(/^#+\s*/, "").trim() || `Section ${idx + 1}`;
        const body = lines.slice(1).join("\n").trim();
        return { title: firstLine, body: body || part.trim() };
      })
      .filter((s) => s.body.length > 0);
  }, [technicalSummaryText]);

  const visibleCrops =
    showAllCrops || cropSearch.trim().length > 0
      ? cropsList
      : cropsList.slice(0, 10);

  const visibleSuburbs =
    showAllSuburbs || suburbSearch.trim().length > 0
      ? suburbsList
      : suburbsList.slice(0, 10);

  const activePdfRows = activePdfTable === "table_1" ? table1Rules : table2Rules;
  const visibleTable1Rules: Record<string, unknown>[] = showAllPdfRules
    ? table1Rules
    : table1Rules.slice(0, 10);
  const visibleTable2Rules: Record<string, unknown>[] = showAllPdfRules
    ? table2Rules
    : table2Rules.slice(0, 10);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Header Introduction */}
      <section className="bg-surface border-2 border-mint rounded-2xl p-6 shadow-sm space-y-2">
        <h1 className="font-display text-2xl sm:text-3xl font-semibold text-ink">
          Reference Datasets &amp; System Architecture
        </h1>
        <p className="text-base text-muted max-w-2xl leading-relaxed">
          Inspect the structured crops, regional soils, PDF tables, and demo fixtures.
        </p>

        {/* Sub-Tab Navigation Bar */}
        <div className="pt-4 flex flex-wrap gap-2 border-t border-sand">
          <button
            type="button"
            onClick={() => setActiveTab("crops")}
            className={`min-h-[44px] px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap inline-flex items-center gap-2 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
              activeTab === "crops"
                ? "bg-forest text-canvas border-2 border-forest"
                : "bg-canvas text-ink border-2 border-mint hover:bg-sand"
            }`}
          >
            <TableIcon />
            <span>1. Crops JSON</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("suburbs")}
            className={`min-h-[44px] px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap inline-flex items-center gap-2 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
              activeTab === "suburbs"
                ? "bg-forest text-canvas border-2 border-forest"
                : "bg-canvas text-ink border-2 border-mint hover:bg-sand"
            }`}
          >
            <TableIcon />
            <span>2. Suburbs CSV</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("pdf_tables")}
            className={`min-h-[44px] px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap inline-flex items-center gap-2 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
              activeTab === "pdf_tables"
                ? "bg-forest text-canvas border-2 border-forest"
                : "bg-canvas text-ink border-2 border-mint hover:bg-sand"
            }`}
          >
            <TableIcon />
            <span>3. PDF Rules</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("part2_demo")}
            className={`min-h-[44px] px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap inline-flex items-center gap-2 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
              activeTab === "part2_demo"
                ? "bg-forest text-canvas border-2 border-forest"
                : "bg-canvas text-ink border-2 border-mint hover:bg-sand"
            }`}
          >
            <CalendarIcon />
            <span>4. Demo Fixtures</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("technical_summary")}
            className={`min-h-[44px] px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap inline-flex items-center gap-2 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
              activeTab === "technical_summary"
                ? "bg-forest text-canvas border-2 border-forest"
                : "bg-canvas text-ink border-2 border-mint hover:bg-sand"
            }`}
          >
            <DocumentIcon />
            <span>5. Architecture</span>
          </button>
        </div>
      </section>

      {/* Source-focus banner: shown when the user arrived here from a citation */}
      {focusTarget && highlightKey && (
        <section
          aria-live="polite"
          className="bg-forest text-canvas rounded-2xl px-5 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm"
        >
          <div className="min-w-0">
            <p className="text-sm font-semibold">Showing the source behind your answer</p>
            <p className="font-mono text-xs text-mint break-words">{focusTarget.label}</p>
          </div>
          {onBackToAnswer && (
            <button
              type="button"
              onClick={onBackToAnswer}
              className="min-h-[44px] px-4 rounded-full bg-canvas text-forest hover:bg-mint text-sm font-semibold whitespace-nowrap self-start sm:self-auto transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-canvas"
            >
              Back to your answer
            </button>
          )}
        </section>
      )}

      {/* SUB-TAB 1: Crop Planting Guide (JSON) */}
      {activeTab === "crops" && (
        <section className="bg-canvas border-2 border-mint rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="font-display text-xl font-semibold text-ink break-words min-w-0">
                Crop Planting Guide (JSON)
              </h2>
              <p className="text-sm text-muted">
                Showing <strong className="tabular-nums text-ink">{visibleCrops.length}</strong> of{" "}
                <strong className="tabular-nums text-ink">{cropsList.length}</strong> verified crops.
              </p>
            </div>

            <div className="relative w-full sm:w-72">
              <input
                type="text"
                value={cropSearch}
                onChange={(e) => setCropSearch(e.target.value)}
                placeholder="Search crops or companions..."
                className="w-full min-h-[44px] pl-10 pr-4 rounded-xl text-sm bg-surface border border-mint text-ink placeholder-muted focus:outline-none focus:ring-2 focus:ring-forest"
              />
              <span className="absolute left-3.5 top-3.5 pointer-events-none">
                <SearchIcon />
              </span>
            </div>
          </div>

          <div className="overflow-x-auto border border-sand rounded-xl">
            <table className="w-full text-left text-sm text-ink">
              <thead className="bg-surface border-b border-sand">
                <tr>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Crop Name
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Scientific Name
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Category
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Optimal Soil pH
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Water Need
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Frost Tolerance
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Companion Crops
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-sand/70">
                {visibleCrops.map((crop, idx) => {
                  const name = String(crop.crop_name || "Unknown");
                  const sci = String(crop.scientific_name || "");
                  const cat = String(crop.category || crop.family || "Vegetable");
                  const phMin = crop.optimal_ph_min ?? crop.soil_ph_min ?? 6.0;
                  const phMax = crop.optimal_ph_max ?? crop.soil_ph_max ?? 7.0;
                  const water = Number(crop.water_mm_per_week ?? 25);
                  const frost = String(
                    crop.frost_tolerance ??
                      (crop.frost_tolerant ? "Tolerant" : "Sensitive")
                  );
                  const companions = Array.isArray(crop.companion_plants)
                    ? crop.companion_plants.join(", ")
                    : String(crop.companion_crops || crop.companion_plants || "General companions");

                  const isHighlighted = highlightKey === `crop:${name.toLowerCase()}`;

                  return (
                    <tr
                      key={idx}
                      data-source-row={`crop:${name.toLowerCase()}`}
                      className={`transition-colors duration-150 ${
                        isHighlighted ? HIGHLIGHT_ROW_CLASS : "hover:bg-surface/60"
                      }`}
                    >
                      <td className="py-3.5 px-4 font-semibold text-ink">
                        {name}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs text-forest italic">
                        {sci}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2.5 py-0.5 rounded bg-surface border border-sand text-muted text-xs">
                          {cat}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-display font-semibold tabular-nums text-ink">
                        {Number(phMin).toFixed(1)} to {Number(phMax).toFixed(1)}
                      </td>
                      <td className="py-3.5 px-4 tabular-nums text-muted">
                        {water} mm/week
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            frost === "Tolerant"
                              ? "bg-mint text-ink"
                              : "bg-surface text-muted border border-sand"
                          }`}
                        >
                          {frost}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-muted text-xs max-w-xs">
                        {companions}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {cropsList.length > 10 && !cropSearch.trim() && (
            <button
              type="button"
              onClick={() => setShowAllCrops((prev) => !prev)}
              className="w-full min-h-[44px] rounded-xl bg-surface hover:bg-sand border border-sand text-sm font-semibold text-forest whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              {showAllCrops
                ? "Show first 10 crops"
                : `Show all ${cropsList.length} crops`}
            </button>
          )}
        </section>
      )}

      {/* SUB-TAB 2: Regional Soil & Climate (CSV) */}
      {activeTab === "suburbs" && (
        <section className="bg-canvas border-2 border-mint rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="font-display text-xl font-semibold text-ink break-words min-w-0">
                Regional Soil &amp; Climate (CSV)
              </h2>
              <p className="text-sm text-muted">
                Showing <strong className="tabular-nums text-ink">{visibleSuburbs.length}</strong> of{" "}
                <strong className="tabular-nums text-ink">{suburbsList.length}</strong> Western Cape suburbs.
              </p>
            </div>

            <div className="relative w-full sm:w-72">
              <input
                type="text"
                value={suburbSearch}
                onChange={(e) => setSuburbSearch(e.target.value)}
                placeholder="Filter suburbs or soil types..."
                className="w-full min-h-[44px] pl-10 pr-4 rounded-xl text-sm bg-surface border border-mint text-ink placeholder-muted focus:outline-none focus:ring-2 focus:ring-forest"
              />
              <span className="absolute left-3.5 top-3.5 pointer-events-none">
                <SearchIcon />
              </span>
            </div>
          </div>

          <div className="overflow-x-auto border border-sand rounded-xl">
            <table className="w-full text-left text-sm text-ink">
              <thead className="bg-surface border-b border-sand">
                <tr>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Suburb
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Soil Type
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Baseline pH
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Summer Rain
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Winter Rain
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Frost Risk
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Microclimate Notes
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-sand/70">
                {visibleSuburbs.map((sub, idx) => {
                  const suburb = String(sub.suburb || "Unknown");
                  const prov = String(sub.province || "Western Cape");
                  const soil = String(sub.soil_type || "sandy_loam");
                  const phRange =
                    sub.baseline_ph_range ||
                    `${sub.baseline_ph_min ?? 5.5} to ${sub.baseline_ph_max ?? 6.5}`;
                  const summer = sub.summer_rain_mm ?? sub.annual_rainfall_mm ?? 20;
                  const winter = sub.winter_rain_mm ?? 80;
                  const frost = String(sub.frost_risk || "None");
                  const notes = String(
                    sub.microclimate_notes || sub.typical_amendment_need || "Mediterranean slope."
                  );

                  const isHighlighted = highlightKey === `suburb:${idx}`;

                  return (
                    <tr
                      key={idx}
                      data-source-row={`suburb:${idx}`}
                      className={`transition-colors duration-150 ${
                        isHighlighted ? HIGHLIGHT_ROW_CLASS : "hover:bg-surface/60"
                      }`}
                    >
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="font-semibold text-ink">{suburb}</div>
                        <div className="text-xs text-muted">{prov}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-mono text-xs px-2.5 py-0.5 rounded bg-surface border border-sand text-forest">
                          {soil}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-display font-semibold tabular-nums text-ink whitespace-nowrap">
                        {String(phRange)}
                      </td>
                      <td className="py-3.5 px-4 tabular-nums text-muted whitespace-nowrap">
                        {String(summer)} mm
                      </td>
                      <td className="py-3.5 px-4 tabular-nums text-muted whitespace-nowrap">
                        {String(winter)} mm
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            frost.toLowerCase() === "none"
                              ? "bg-mint text-ink"
                              : "bg-ochre/20 text-ink border border-ochre/40"
                          }`}
                        >
                          {frost}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-muted text-xs max-w-sm">
                        {notes}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {suburbsList.length > 10 && !suburbSearch.trim() && (
            <button
              type="button"
              onClick={() => setShowAllSuburbs((prev) => !prev)}
              className="w-full min-h-[44px] rounded-xl bg-surface hover:bg-sand border border-sand text-sm font-semibold text-forest whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              {showAllSuburbs
                ? "Show first 10 suburbs"
                : `Show all ${suburbsList.length} suburbs`}
            </button>
          )}
        </section>
      )}

      {/* SUB-TAB 3: Soil Treatment & Watering Rules (PDF Tables) */}
      {activeTab === "pdf_tables" && (
        <section className="bg-canvas border-2 border-mint rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="font-display text-xl font-semibold text-ink break-words min-w-0">
                Soil Treatment &amp; Watering Rules (PDF)
              </h2>
              <p className="text-sm text-muted">
                Showing{" "}
                <strong className="tabular-nums text-ink">
                  {(activePdfTable === "table_1" ? visibleTable1Rules : visibleTable2Rules).length}
                </strong>{" "}
                of <strong className="tabular-nums text-ink">{activePdfRows.length}</strong> extracted PDF rules.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setActivePdfTable("table_1");
                  setShowAllPdfRules(false);
                }}
                className={`min-h-[44px] px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap border transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
                  activePdfTable === "table_1"
                    ? "bg-forest text-canvas border-forest"
                    : "bg-surface hover:bg-sand text-ink border-mint"
                }`}
              >
                Table 1: Soil pH Rules
              </button>

              <button
                type="button"
                onClick={() => {
                  setActivePdfTable("table_2");
                  setShowAllPdfRules(false);
                }}
                className={`min-h-[44px] px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap border transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
                  activePdfTable === "table_2"
                    ? "bg-forest text-canvas border-forest"
                    : "bg-surface hover:bg-sand text-ink border-mint"
                }`}
              >
                Table 2: Watering Rules
              </button>
            </div>
          </div>

          {activePdfTable === "table_1" ? (
            <div className="overflow-x-auto border border-sand rounded-xl">
              <table className="w-full text-left text-sm text-ink">
                <thead className="bg-surface border-b border-sand">
                  <tr>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Rule ID
                    </th>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Soil Type
                    </th>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      pH Bracket
                    </th>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Amendment
                    </th>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Dosage
                    </th>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Application Notes
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-sand/70">
                  {visibleTable1Rules.map((rule, idx) => {
                    const isHighlighted = highlightKey === `table_1:${idx}`;
                    return (
                      <tr
                        key={idx}
                        data-source-row={`table_1:${idx}`}
                        className={`transition-colors duration-150 ${
                          isHighlighted ? HIGHLIGHT_ROW_CLASS : "hover:bg-surface/60"
                        }`}
                      >
                        <td className="py-3.5 px-4 font-mono font-semibold text-forest">
                          {String(rule.rule_id || `RULE-PH-${idx + 1}`)}
                        </td>
                        <td className="py-3.5 px-4 font-mono text-xs text-ink">
                          {String(rule.soil_type || "")}
                        </td>
                        <td className="py-3.5 px-4 font-display font-semibold tabular-nums text-ink">
                          {String(rule.current_ph_bracket || "")}
                        </td>
                        <td className="py-3.5 px-4 font-semibold text-ink">
                          {String(rule.amendment_type || "")}
                        </td>
                        <td className="py-3.5 px-4 font-display font-semibold tabular-nums text-forest">
                          {String(rule.dosage_g_per_m2 || "")} g/m2
                        </td>
                        <td className="py-3.5 px-4 text-muted text-xs max-w-sm">
                          {String(rule.application_notes || "")}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="overflow-x-auto border border-sand rounded-xl">
              <table className="w-full text-left text-sm text-ink">
                <thead className="bg-surface border-b border-sand">
                  <tr>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Rule ID
                    </th>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Temp (C)
                    </th>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Rain (mm)
                    </th>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Soil Type
                    </th>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Water Adj
                    </th>
                    <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                      Mulching Recommendation
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-sand/70">
                  {visibleTable2Rules.map((rule, idx) => {
                    const isHighlighted = highlightKey === `table_2:${idx}`;
                    return (
                      <tr
                        key={idx}
                        data-source-row={`table_2:${idx}`}
                        className={`transition-colors duration-150 ${
                          isHighlighted ? HIGHLIGHT_ROW_CLASS : "hover:bg-surface/60"
                        }`}
                      >
                        <td className="py-3.5 px-4 font-mono font-semibold text-forest">
                          {String(rule.rule_id || `RULE-WT-${idx + 1}`)}
                        </td>
                        <td className="py-3.5 px-4 font-display tabular-nums text-ink">
                          {String(rule.temp_bracket_c || "")}
                        </td>
                        <td className="py-3.5 px-4 tabular-nums text-muted">
                          {String(rule.rainfall_bracket_mm || "")}
                        </td>
                        <td className="py-3.5 px-4 font-mono text-xs text-ink">
                          {String(rule.soil_type || "")}
                        </td>
                        <td className="py-3.5 px-4 font-display font-semibold tabular-nums text-forest">
                          {String(rule.weekly_water_adjustment_mm || "")} mm
                        </td>
                        <td className="py-3.5 px-4 text-muted text-xs max-w-sm">
                          {String(rule.mulching_recommendation || "")}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {activePdfRows.length > 10 && (
            <button
              type="button"
              onClick={() => setShowAllPdfRules((prev) => !prev)}
              className="w-full min-h-[44px] rounded-xl bg-surface hover:bg-sand border border-sand text-sm font-semibold text-forest whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              {showAllPdfRules
                ? "Show first 10 rules"
                : `Show all ${activePdfRows.length} rules`}
            </button>
          )}
        </section>
      )}

      {/* SUB-TAB 4: Part 2 Demo Inbox & Calendar */}
      {activeTab === "part2_demo" && (
        <section className="bg-canvas border-2 border-mint rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="font-display text-xl font-semibold text-ink break-words min-w-0">
                Part 2 Ingestion Fixtures
              </h2>
              <p className="text-sm text-muted">
                Scheduled plot bookings and raw gardener emails used by the Verification Agent.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setActiveDemoSubTab("calendar")}
                className={`min-h-[44px] px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap border transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
                  activeDemoSubTab === "calendar"
                    ? "bg-forest text-canvas border-forest"
                    : "bg-surface hover:bg-sand text-ink border-mint"
                }`}
              >
                Calendar Events (8)
              </button>

              <button
                type="button"
                onClick={() => setActiveDemoSubTab("emails")}
                className={`min-h-[44px] px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap border transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
                  activeDemoSubTab === "emails"
                    ? "bg-forest text-canvas border-forest"
                    : "bg-surface hover:bg-sand text-ink border-mint"
                }`}
              >
                Gardener Emails (10)
              </button>
            </div>
          </div>

          {activeDemoSubTab === "calendar" ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {calendarEvents.map((event) => (
                <div
                  key={event.event_id}
                  className="bg-surface border border-sand rounded-xl p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-forest">
                      {event.event_id}
                    </span>
                    <span className="font-mono text-xs tabular-nums text-muted">
                      {event.scheduled_date}
                    </span>
                  </div>
                  <p className="font-semibold text-sm text-ink">
                    {event.gardener_name}
                  </p>
                  <div className="flex items-center justify-between text-xs pt-2 border-t border-sand">
                    <span className="font-mono font-semibold text-ink">
                      {event.plot_id}
                    </span>
                    <span className="text-forest font-medium">{event.suburb}</span>
                  </div>
                  <p className="text-xs text-muted leading-relaxed pt-1">
                    {event.notes}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {gardenerEmails.map((email) => {
                const isExpanded = expandedEmails[email.email_id] ?? false;
                return (
                  <div
                    key={email.email_id}
                    className="bg-surface border border-sand rounded-xl p-4 space-y-2.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-forest">
                        {email.email_id}
                      </span>
                      <span className="font-mono text-xs tabular-nums text-muted">
                        {email.received_at.split("T")[0]}{" "}
                        {email.received_at.split("T")[1]?.slice(0, 5)}
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-ink">
                      {email.subject}
                    </p>
                    <p className="text-xs text-muted">
                      From: <strong className="text-ink">{email.sender_name}</strong>
                    </p>
                    <p
                      className={`text-sm text-ink bg-canvas p-3 rounded-lg border border-sand leading-relaxed ${
                        !isExpanded ? "line-clamp-2" : ""
                      }`}
                    >
                      &quot;{email.body}&quot;
                    </p>
                    {email.body.length > 110 && (
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedEmails((prev) => ({
                            ...prev,
                            [email.email_id]: !prev[email.email_id],
                          }))
                        }
                        className="min-h-[44px] text-xs font-semibold text-forest hover:text-ink whitespace-nowrap focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                      >
                        {isExpanded ? "Show less" : "Read full email"}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </section>
      )}

      {/* SUB-TAB 5: Technical Summary (Collapsible Section Cards) */}
      {activeTab === "technical_summary" && (
        <section className="bg-canvas border-2 border-mint rounded-2xl p-6 sm:p-8 shadow-sm space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-sand pb-4">
            <div>
              <h2 className="font-display text-xl font-semibold text-ink">
                Engineering Architecture &amp; Agronomic Rules
              </h2>
              <p className="text-sm text-muted mt-0.5">
                Expand any section below to read the full technical details.
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                const allOpen = summarySections.every((_, i) => expandedSections[i]);
                const next: Record<number, boolean> = {};
                summarySections.forEach((_, i) => {
                  next[i] = !allOpen;
                });
                setExpandedSections(next);
              }}
              className="min-h-[44px] px-4 py-1.5 rounded-full bg-surface hover:bg-sand border border-sand text-xs font-semibold text-forest whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              {summarySections.every((_, i) => expandedSections[i])
                ? "Collapse sections"
                : "Expand all sections"}
            </button>
          </div>

          <div className="space-y-3">
            {summarySections.map((sec, idx) => {
              const isOpen = expandedSections[idx] ?? false;
              return (
                <div
                  key={idx}
                  className="bg-surface border border-sand rounded-xl overflow-hidden"
                >
                  <button
                    type="button"
                    onClick={(e) => {
                      const card = e.currentTarget.parentElement;
                      setExpandedSections((prev) => {
                        const next = !prev[idx];
                        if (next) scrollIntoFrame(card);
                        return {
                          ...prev,
                          [idx]: next,
                        };
                      });
                    }}
                    className="w-full min-h-[44px] px-5 py-3.5 flex items-center justify-between gap-3 text-left hover:bg-sand/50 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                  >
                    <span className="font-display text-base sm:text-lg font-semibold text-ink">
                      {sec.title}
                    </span>
                    <span className="text-xs font-semibold text-forest whitespace-nowrap">
                      {isOpen ? "Hide" : "Read section"}
                    </span>
                  </button>
                  {isOpen && (
                    <div className="px-5 pb-5 pt-2 border-t border-sand text-sm leading-relaxed text-ink whitespace-pre-wrap font-sans">
                      {sec.body}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
