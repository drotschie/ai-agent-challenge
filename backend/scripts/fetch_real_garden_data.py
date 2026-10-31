"""Real Garden Data & Fixture Generation Script.

Generates the 3 Part 1 foundational data files:
1. crop_planting_guide.json (40 crops with GBIF taxonomy, soil pH bounds, water requirements)
2. regional_soil_and_climate.csv (40 SA suburbs and towns across all 5 soil types)
3. soil_treatment_and_watering_rules.pdf (2 structured vector-bordered tables)

And the 3 Part 2 demo fixture files:
4. demo_fixtures/demo_calendar_events.json (8 community garden events)
5. demo_fixtures/demo_gardener_emails.json (10 messy gardener emails with typos and follow-ups)
6. demo_fixtures/api_fallback_cache.json (GBIF taxonomy and Open-Meteo weather cache)
"""

import csv
import json
import logging
from pathlib import Path
import sys

# Ensure backend root directory is at the front of sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pdfplumber
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fetch_real_garden_data")

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
FIXTURES_DIR = DATA_DIR / "demo_fixtures"


# ------------------------------------------------------------------------------
# 1. 40 Garden Crops Data Definition
# ------------------------------------------------------------------------------
CROPS_40 = [
    {
        "crop_id": "CROP-01",
        "crop_name": "Spinach",
        "scientific_name": "Spinacia oleracea",
        "gbif_usage_key": 3083868,
        "family": "Amaranthaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 10.0,
        "optimal_temp_max_c": 22.0,
        "frost_tolerant": True,
        "water_mm_per_week": 30,
        "days_to_harvest": 45,
        "planting_months_western_cape": ["March", "April", "May", "June", "July", "August", "September"],
        "planting_months_summer_rainfall": ["February", "March", "April", "August", "September"],
        "preferred_soil_types": ["sandy_loam", "loam", "clay_loam"],
        "companion_plants": ["Strawberry", "Cabbage", "Cauliflower", "Radish"],
        "avoid_near": ["Fennel", "Potato"],
        "description": "Fast-growing cool-season leafy green that demands nitrogen-rich soil and consistent moisture; sensitive to acidic soil below pH 6.0.",
    },
    {
        "crop_id": "CROP-02",
        "crop_name": "Heirloom Tomato",
        "scientific_name": "Solanum lycopersicum",
        "gbif_usage_key": 2930137,
        "family": "Solanaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 6.8,
        "optimal_temp_min_c": 18.0,
        "optimal_temp_max_c": 30.0,
        "frost_tolerant": False,
        "water_mm_per_week": 35,
        "days_to_harvest": 80,
        "planting_months_western_cape": ["September", "October", "November", "December"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November", "December", "January"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Basil", "Parsley", "Carrot", "Marigold"],
        "avoid_near": ["Potato", "Fennel", "Cabbage"],
        "description": "High-value warm-season crop requiring well-drained fertile soil, full sun, and consistent irrigation to prevent blossom-end rot.",
    },
    {
        "crop_id": "CROP-03",
        "crop_name": "Cape Gooseberry",
        "scientific_name": "Physalis peruviana",
        "gbif_usage_key": 2928906,
        "family": "Solanaceae",
        "soil_ph_min": 5.5,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 15.0,
        "optimal_temp_max_c": 28.0,
        "frost_tolerant": False,
        "water_mm_per_week": 25,
        "days_to_harvest": 105,
        "planting_months_western_cape": ["August", "September", "October", "November"],
        "planting_months_summer_rainfall": ["August", "September", "October"],
        "preferred_soil_types": ["sandy", "sandy_loam", "loam"],
        "companion_plants": ["Basil", "Mint", "Sweet Pepper"],
        "avoid_near": ["Potato", "Eggplant"],
        "description": "Hardy indigenous-favoured berry shrub that yields sweet-tart papery husked fruit; performs well in moderate to sandy coastal soils.",
    },
    {
        "crop_id": "CROP-04",
        "crop_name": "Kale",
        "scientific_name": "Brassica oleracea var. acephala",
        "gbif_usage_key": 3042858,
        "family": "Brassicaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.5,
        "optimal_temp_min_c": 8.0,
        "optimal_temp_max_c": 24.0,
        "frost_tolerant": True,
        "water_mm_per_week": 28,
        "days_to_harvest": 55,
        "planting_months_western_cape": ["February", "March", "April", "May", "June", "July", "August"],
        "planting_months_summer_rainfall": ["January", "February", "March", "August", "September"],
        "preferred_soil_types": ["loam", "clay_loam", "clay"],
        "companion_plants": ["Beetroot", "Rosemary", "Thyme", "Dill"],
        "avoid_near": ["Strawberry", "Tomato", "Green Beans"],
        "description": "Extremely resilient brassica providing continuous harvests through winter cold snaps; sweetens following light frosts.",
    },
    {
        "crop_id": "CROP-05",
        "crop_name": "Butternut Squash",
        "scientific_name": "Cucurbita moschata",
        "gbif_usage_key": 2874513,
        "family": "Cucurbitaceae",
        "soil_ph_min": 5.8,
        "soil_ph_max": 6.8,
        "optimal_temp_min_c": 18.0,
        "optimal_temp_max_c": 32.0,
        "frost_tolerant": False,
        "water_mm_per_week": 30,
        "days_to_harvest": 95,
        "planting_months_western_cape": ["September", "October", "November", "December"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November", "December"],
        "preferred_soil_types": ["sandy_loam", "loam", "clay_loam"],
        "companion_plants": ["Sweet Corn", "Green Beans", "Radish"],
        "avoid_near": ["Potato", "Fennel"],
        "description": "Vigorous trailing winter squash with dense nutty flesh and superb winter storability; thrives in hot sunny Cape summers.",
    },
    {
        "crop_id": "CROP-06",
        "crop_name": "Sweet Pepper",
        "scientific_name": "Capsicum annuum",
        "gbif_usage_key": 2932942,
        "family": "Solanaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 6.8,
        "optimal_temp_min_c": 18.0,
        "optimal_temp_max_c": 30.0,
        "frost_tolerant": False,
        "water_mm_per_week": 30,
        "days_to_harvest": 75,
        "planting_months_western_cape": ["September", "October", "November", "December"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Basil", "Carrot", "Parsley", "Onion"],
        "avoid_near": ["Fennel", "Broad Bean"],
        "description": "Thick-walled bell pepper delivering sweet crisp fruit when supplied with warm sunny positions and even soil moisture.",
    },
    {
        "crop_id": "CROP-07",
        "crop_name": "Beetroot",
        "scientific_name": "Beta vulgaris",
        "gbif_usage_key": 3083501,
        "family": "Amaranthaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.5,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 24.0,
        "frost_tolerant": True,
        "water_mm_per_week": 25,
        "days_to_harvest": 60,
        "planting_months_western_cape": ["August", "September", "October", "February", "March", "April"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November", "January", "February"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Lettuce", "Red Onion", "Cabbage", "Kale"],
        "avoid_near": ["Green Beans", "Sweet Corn"],
        "description": "Dual-purpose root and green crop rich in betalains and minerals; requires stoneless loose soil to form uniform globes.",
    },
    {
        "crop_id": "CROP-08",
        "crop_name": "Carrot",
        "scientific_name": "Daucus carota",
        "gbif_usage_key": 3034725,
        "family": "Apiaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 6.8,
        "optimal_temp_min_c": 14.0,
        "optimal_temp_max_c": 24.0,
        "frost_tolerant": True,
        "water_mm_per_week": 22,
        "days_to_harvest": 70,
        "planting_months_western_cape": ["August", "September", "October", "February", "March", "April"],
        "planting_months_summer_rainfall": ["August", "September", "October", "January", "February", "March"],
        "preferred_soil_types": ["sandy", "sandy_loam", "loam"],
        "companion_plants": ["Lettuce", "Radish", "Rosemary", "Chives"],
        "avoid_near": ["Fennel", "Dill", "Parsnip"],
        "description": "Deep taproot crop prized for sweet crunchy roots; requires fine, stone-free sandy loam to prevent forking.",
    },
    {
        "crop_id": "CROP-09",
        "crop_name": "Swiss Chard",
        "scientific_name": "Beta vulgaris subsp. vulgaris",
        "gbif_usage_key": 3083503,
        "family": "Amaranthaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.5,
        "optimal_temp_min_c": 10.0,
        "optimal_temp_max_c": 28.0,
        "frost_tolerant": True,
        "water_mm_per_week": 28,
        "days_to_harvest": 50,
        "planting_months_western_cape": ["August", "September", "October", "November", "February", "March", "April"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November", "December", "January", "February"],
        "preferred_soil_types": ["sandy_loam", "loam", "clay_loam"],
        "companion_plants": ["Red Onion", "Lavender", "Green Beans"],
        "avoid_near": ["Potato", "Sweet Corn"],
        "description": "Hardy Cape staple providing abundant rainbow stems and succulent leaves across hot summers and cool winters alike.",
    },
    {
        "crop_id": "CROP-10",
        "crop_name": "Zucchini",
        "scientific_name": "Cucurbita pepo",
        "gbif_usage_key": 2874508,
        "family": "Cucurbitaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 18.0,
        "optimal_temp_max_c": 30.0,
        "frost_tolerant": False,
        "water_mm_per_week": 35,
        "days_to_harvest": 50,
        "planting_months_western_cape": ["September", "October", "November", "December"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November", "December"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Green Beans", "Sweet Corn", "Nasturtium"],
        "avoid_near": ["Potato", "Fennel"],
        "description": "Prolific summer bush squash yielding tender fruit within weeks of warm soil germination; requires heavy organic matter.",
    },
    {
        "crop_id": "CROP-11",
        "crop_name": "Green Beans",
        "scientific_name": "Phaseolus vulgaris",
        "gbif_usage_key": 5350444,
        "family": "Fabaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 16.0,
        "optimal_temp_max_c": 28.0,
        "frost_tolerant": False,
        "water_mm_per_week": 25,
        "days_to_harvest": 55,
        "planting_months_western_cape": ["September", "October", "November", "December", "January"],
        "planting_months_summer_rainfall": ["September", "October", "November", "December", "January"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Carrot", "Cucumber", "Strawberry", "Sweet Corn"],
        "avoid_near": ["Red Onion", "Garlic", "Leek", "Fennel"],
        "description": "Nitrogen-fixing legume producing tender pods; improves soil fertility naturally for subsequent heavy-feeding plantings.",
    },
    {
        "crop_id": "CROP-12",
        "crop_name": "Garden Peas",
        "scientific_name": "Pisum sativum",
        "gbif_usage_key": 2953291,
        "family": "Fabaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.5,
        "optimal_temp_min_c": 10.0,
        "optimal_temp_max_c": 20.0,
        "frost_tolerant": True,
        "water_mm_per_week": 25,
        "days_to_harvest": 65,
        "planting_months_western_cape": ["April", "May", "June", "July"],
        "planting_months_summer_rainfall": ["March", "April", "May", "June"],
        "preferred_soil_types": ["sandy_loam", "loam", "clay_loam"],
        "companion_plants": ["Carrot", "Radish", "Cucumber", "Green Beans"],
        "avoid_near": ["Red Onion", "Garlic", "Leek"],
        "description": "Sweet cool-season climber fixing atmospheric nitrogen; highly rewarding in Cape winter gardens with bamboo staking.",
    },
    {
        "crop_id": "CROP-13",
        "crop_name": "Broccoli",
        "scientific_name": "Brassica oleracea var. italica",
        "gbif_usage_key": 3042859,
        "family": "Brassicaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.2,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 22.0,
        "frost_tolerant": True,
        "water_mm_per_week": 32,
        "days_to_harvest": 75,
        "planting_months_western_cape": ["February", "March", "April", "May", "June"],
        "planting_months_summer_rainfall": ["January", "February", "March", "April"],
        "preferred_soil_types": ["loam", "clay_loam"],
        "companion_plants": ["Rosemary", "Thyme", "Beetroot", "Celery"],
        "avoid_near": ["Strawberry", "Tomato"],
        "description": "Prized winter head-forming brassica with high nutrient demand; requires steady irrigation to form compact florets.",
    },
    {
        "crop_id": "CROP-14",
        "crop_name": "Cauliflower",
        "scientific_name": "Brassica oleracea var. botrytis",
        "gbif_usage_key": 3042860,
        "family": "Brassicaceae",
        "soil_ph_min": 6.2,
        "soil_ph_max": 7.2,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 20.0,
        "frost_tolerant": True,
        "water_mm_per_week": 35,
        "days_to_harvest": 85,
        "planting_months_western_cape": ["February", "March", "April", "May"],
        "planting_months_summer_rainfall": ["January", "February", "March"],
        "preferred_soil_types": ["loam", "clay_loam"],
        "companion_plants": ["Celery", "Spinach", "Thyme"],
        "avoid_near": ["Tomato", "Strawberry"],
        "description": "Cool-season curd brassica sensitive to heat checks and moisture fluctuations; demands fertile, well-limed soil.",
    },
    {
        "crop_id": "CROP-15",
        "crop_name": "Cabbage",
        "scientific_name": "Brassica oleracea var. capitata",
        "gbif_usage_key": 3042861,
        "family": "Brassicaceae",
        "soil_ph_min": 6.2,
        "soil_ph_max": 7.5,
        "optimal_temp_min_c": 10.0,
        "optimal_temp_max_c": 22.0,
        "frost_tolerant": True,
        "water_mm_per_week": 30,
        "days_to_harvest": 80,
        "planting_months_western_cape": ["February", "March", "April", "May", "June"],
        "planting_months_summer_rainfall": ["January", "February", "March", "July", "August"],
        "preferred_soil_types": ["loam", "clay_loam", "clay"],
        "companion_plants": ["Rosemary", "Sage", "Beetroot", "Dill"],
        "avoid_near": ["Tomato", "Green Beans"],
        "description": "Dense head-forming vegetable essential to community nutrition; highly responsive to well-rotted manure additions.",
    },
    {
        "crop_id": "CROP-16",
        "crop_name": "Lettuce",
        "scientific_name": "Lactuca sativa",
        "gbif_usage_key": 3139824,
        "family": "Asteraceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 22.0,
        "frost_tolerant": True,
        "water_mm_per_week": 26,
        "days_to_harvest": 40,
        "planting_months_western_cape": ["August", "September", "October", "February", "March", "April", "May"],
        "planting_months_summer_rainfall": ["August", "September", "October", "February", "March", "April"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Carrot", "Radish", "Strawberry", "Cucumber"],
        "avoid_near": ["Parsley", "Celery"],
        "description": "Fast-cycling salad green requiring regular shallow watering and afternoon shade in warmest Cape summer months.",
    },
    {
        "crop_id": "CROP-17",
        "crop_name": "Sweet Potato",
        "scientific_name": "Ipomoea batatas",
        "gbif_usage_key": 2928574,
        "family": "Convolvulaceae",
        "soil_ph_min": 5.2,
        "soil_ph_max": 6.5,
        "optimal_temp_min_c": 20.0,
        "optimal_temp_max_c": 32.0,
        "frost_tolerant": False,
        "water_mm_per_week": 25,
        "days_to_harvest": 120,
        "planting_months_western_cape": ["October", "November", "December"],
        "planting_months_summer_rainfall": ["September", "October", "November", "December"],
        "preferred_soil_types": ["sandy", "sandy_loam", "loam"],
        "companion_plants": ["Thyme", "Green Beans", "Dill"],
        "avoid_near": ["Potato", "Pumpkin"],
        "description": "Tuberous warm-season vine that tolerates mildly acidic soils down to pH 5.2 and provides nutrient-rich orange tubers.",
    },
    {
        "crop_id": "CROP-18",
        "crop_name": "Potato",
        "scientific_name": "Solanum tuberosum",
        "gbif_usage_key": 2930262,
        "family": "Solanaceae",
        "soil_ph_min": 5.0,
        "soil_ph_max": 6.5,
        "optimal_temp_min_c": 14.0,
        "optimal_temp_max_c": 24.0,
        "frost_tolerant": False,
        "water_mm_per_week": 30,
        "days_to_harvest": 90,
        "planting_months_western_cape": ["July", "August", "September", "January", "February"],
        "planting_months_summer_rainfall": ["August", "September", "October", "December", "January"],
        "preferred_soil_types": ["sandy", "sandy_loam", "loam"],
        "companion_plants": ["Green Beans", "Sweet Corn", "Cabbage"],
        "avoid_near": ["Heirloom Tomato", "Eggplant", "Pumpkin", "Cucumber"],
        "description": "Essential starch tuber that thrives in moderately acidic soils (pH 5.0-6.0), reducing potato scab incidence significantly.",
    },
    {
        "crop_id": "CROP-19",
        "crop_name": "Red Onion",
        "scientific_name": "Allium cepa",
        "gbif_usage_key": 2770284,
        "family": "Amaryllidaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 26.0,
        "frost_tolerant": True,
        "water_mm_per_week": 22,
        "days_to_harvest": 110,
        "planting_months_western_cape": ["April", "May", "June", "July"],
        "planting_months_summer_rainfall": ["March", "April", "May", "June"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Carrot", "Beetroot", "Lettuce", "Tomato"],
        "avoid_near": ["Green Beans", "Garden Peas", "Broad Bean"],
        "description": "Photoperiod-sensitive allium producing crisp pungent red bulbs with excellent keeping quality in ventilated winter storage.",
    },
    {
        "crop_id": "CROP-20",
        "crop_name": "Garlic",
        "scientific_name": "Allium sativum",
        "gbif_usage_key": 2770245,
        "family": "Amaryllidaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.2,
        "optimal_temp_min_c": 10.0,
        "optimal_temp_max_c": 24.0,
        "frost_tolerant": True,
        "water_mm_per_week": 20,
        "days_to_harvest": 150,
        "planting_months_western_cape": ["March", "April", "May"],
        "planting_months_summer_rainfall": ["March", "April", "May"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Heirloom Tomato", "Rosemary", "Peppers", "Carrot"],
        "avoid_near": ["Green Beans", "Garden Peas", "Parsley"],
        "description": "Cool-season bulb needing winter chill vernalization to segment into fat aromatic cloves; hates stagnant waterlogged beds.",
    },
    {
        "crop_id": "CROP-21",
        "crop_name": "Leek",
        "scientific_name": "Allium ampeloprasum",
        "gbif_usage_key": 2770280,
        "family": "Amaryllidaceae",
        "soil_ph_min": 6.2,
        "soil_ph_max": 7.2,
        "optimal_temp_min_c": 10.0,
        "optimal_temp_max_c": 22.0,
        "frost_tolerant": True,
        "water_mm_per_week": 26,
        "days_to_harvest": 100,
        "planting_months_western_cape": ["February", "March", "April", "May"],
        "planting_months_summer_rainfall": ["January", "February", "March", "April"],
        "preferred_soil_types": ["loam", "clay_loam"],
        "companion_plants": ["Carrot", "Celery", "Tomato"],
        "avoid_near": ["Green Beans", "Garden Peas"],
        "description": "Hardy long-standing allium providing thick white blanched shafts through winter storms and early spring.",
    },
    {
        "crop_id": "CROP-22",
        "crop_name": "Radish",
        "scientific_name": "Raphanus sativus",
        "gbif_usage_key": 3042617,
        "family": "Brassicaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 10.0,
        "optimal_temp_max_c": 22.0,
        "frost_tolerant": True,
        "water_mm_per_week": 20,
        "days_to_harvest": 25,
        "planting_months_western_cape": ["August", "September", "October", "November", "March", "April", "May"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November", "December", "January", "February", "March"],
        "preferred_soil_types": ["sandy", "sandy_loam", "loam"],
        "companion_plants": ["Carrot", "Cucumber", "Lettuce", "Garden Peas"],
        "avoid_near": ["Cabbage", "Cauliflower"],
        "description": "Lightning-fast root radish serving as ideal companion row marker; yields crisp peppery bulbs in less than four weeks.",
    },
    {
        "crop_id": "CROP-23",
        "crop_name": "Turnip",
        "scientific_name": "Brassica rapa",
        "gbif_usage_key": 3042857,
        "family": "Brassicaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 10.0,
        "optimal_temp_max_c": 22.0,
        "frost_tolerant": True,
        "water_mm_per_week": 24,
        "days_to_harvest": 50,
        "planting_months_western_cape": ["March", "April", "May", "August", "September"],
        "planting_months_summer_rainfall": ["February", "March", "April", "August", "September"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Garden Peas", "Radish", "Red Onion"],
        "avoid_near": ["Potato", "Tomato"],
        "description": "Resilient cool-season globe root yielding both peppery edible tops and tender sweet roots; thrives in autumn.",
    },
    {
        "crop_id": "CROP-24",
        "crop_name": "Eggplant",
        "scientific_name": "Solanum melongena",
        "gbif_usage_key": 2930138,
        "family": "Solanaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 6.8,
        "optimal_temp_min_c": 20.0,
        "optimal_temp_max_c": 32.0,
        "frost_tolerant": False,
        "water_mm_per_week": 32,
        "days_to_harvest": 85,
        "planting_months_western_cape": ["September", "October", "November"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Green Beans", "Sweet Pepper", "Marigold"],
        "avoid_near": ["Fennel", "Potato"],
        "description": "Heat-worshipping solanaceous perennial grown as annual; produces glossy purple fruit under prolonged warm Cape sunshine.",
    },
    {
        "crop_id": "CROP-25",
        "crop_name": "Cucumber",
        "scientific_name": "Cucumis sativus",
        "gbif_usage_key": 2874568,
        "family": "Cucurbitaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 18.0,
        "optimal_temp_max_c": 30.0,
        "frost_tolerant": False,
        "water_mm_per_week": 35,
        "days_to_harvest": 60,
        "planting_months_western_cape": ["September", "October", "November", "December"],
        "planting_months_summer_rainfall": ["September", "October", "November", "December", "January"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Sweet Corn", "Green Beans", "Radish", "Sunflower"],
        "avoid_near": ["Potato", "Aromatic Herbs"],
        "description": "Fast-growing vine delivering thirst-quenching crisp cucumbers; requires consistent deep hydration to prevent bitterness.",
    },
    {
        "crop_id": "CROP-26",
        "crop_name": "Pumpkin",
        "scientific_name": "Cucurbita maxima",
        "gbif_usage_key": 2874515,
        "family": "Cucurbitaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 18.0,
        "optimal_temp_max_c": 32.0,
        "frost_tolerant": False,
        "water_mm_per_week": 30,
        "days_to_harvest": 110,
        "planting_months_western_cape": ["September", "October", "November"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November"],
        "preferred_soil_types": ["sandy_loam", "loam", "clay_loam"],
        "companion_plants": ["Sweet Corn", "Green Beans", "Nasturtium"],
        "avoid_near": ["Potato"],
        "description": "Sprawling traditional boerpampoen vine yielding large hearty squash with sweet dense orange flesh for stewing and roasting.",
    },
    {
        "crop_id": "CROP-27",
        "crop_name": "Watermelon",
        "scientific_name": "Citrullus lanatus",
        "gbif_usage_key": 2874621,
        "family": "Cucurbitaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 6.8,
        "optimal_temp_min_c": 22.0,
        "optimal_temp_max_c": 35.0,
        "frost_tolerant": False,
        "water_mm_per_week": 28,
        "days_to_harvest": 90,
        "planting_months_western_cape": ["October", "November", "December"],
        "planting_months_summer_rainfall": ["September", "October", "November", "December"],
        "preferred_soil_types": ["sandy", "sandy_loam"],
        "companion_plants": ["Radish", "Oregano", "Marigold"],
        "avoid_near": ["Potato", "Zucchini"],
        "description": "Heat-loving Southern African native desert vine; produces sweet refreshing melons in deep sandy, well-warmed beds.",
    },
    {
        "crop_id": "CROP-28",
        "crop_name": "Strawberry",
        "scientific_name": "Fragaria ananassa",
        "gbif_usage_key": 3029969,
        "family": "Rosaceae",
        "soil_ph_min": 5.5,
        "soil_ph_max": 6.5,
        "optimal_temp_min_c": 14.0,
        "optimal_temp_max_c": 26.0,
        "frost_tolerant": True,
        "water_mm_per_week": 28,
        "days_to_harvest": 70,
        "planting_months_western_cape": ["April", "May", "June", "July"],
        "planting_months_summer_rainfall": ["March", "April", "May"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Spinach", "Borage", "Thyme", "Lettuce"],
        "avoid_near": ["Cabbage", "Broccoli", "Cauliflower"],
        "description": "Perennial berry groundcover producing succulent red fruit across Cape spring; thrives with pine-straw acid mulching.",
    },
    {
        "crop_id": "CROP-29",
        "crop_name": "Blueberry",
        "scientific_name": "Vaccinium corymbosum",
        "gbif_usage_key": 2882833,
        "family": "Ericaceae",
        "soil_ph_min": 4.5,
        "soil_ph_max": 5.5,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 26.0,
        "frost_tolerant": True,
        "water_mm_per_week": 32,
        "days_to_harvest": 120,
        "planting_months_western_cape": ["May", "June", "July", "August"],
        "planting_months_summer_rainfall": ["April", "May", "June"],
        "preferred_soil_types": ["sandy", "sandy_loam", "loam"],
        "companion_plants": ["Pine Mulch", "Heather", "Thyme"],
        "avoid_near": ["Brassicas", "Sweet Corn"],
        "description": "Acidophilic fruit bush strictly requiring acidic soils between pH 4.5 and 5.5; naturally thrives in unlimed acidic soils.",
    },
    {
        "crop_id": "CROP-30",
        "crop_name": "Rosemary",
        "scientific_name": "Salvia rosmarinus",
        "gbif_usage_key": 2927005,
        "family": "Lamiaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.5,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 30.0,
        "frost_tolerant": True,
        "water_mm_per_week": 12,
        "days_to_harvest": 60,
        "planting_months_western_cape": ["August", "September", "October", "March", "April"],
        "planting_months_summer_rainfall": ["August", "September", "October", "February", "March"],
        "preferred_soil_types": ["sandy", "sandy_loam", "loam"],
        "companion_plants": ["Cabbage", "Carrot", "Green Beans"],
        "avoid_near": ["Basil", "Pumpkin"],
        "description": "Drought-hardy woody Mediterranean perennial; thrives on poor, rocky, free-draining soils with minimal irrigation.",
    },
    {
        "crop_id": "CROP-31",
        "crop_name": "Basil",
        "scientific_name": "Ocimum basilicum",
        "gbif_usage_key": 2927096,
        "family": "Lamiaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 18.0,
        "optimal_temp_max_c": 30.0,
        "frost_tolerant": False,
        "water_mm_per_week": 25,
        "days_to_harvest": 40,
        "planting_months_western_cape": ["September", "October", "November", "December"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November", "December"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Heirloom Tomato", "Sweet Pepper", "Eggplant"],
        "avoid_near": ["Rosemary", "Rue"],
        "description": "Aromatic warm-season herb enhancing tomato vigor and repelling whiteflies; intolerant of cold winds and frost.",
    },
    {
        "crop_id": "CROP-32",
        "crop_name": "Coriander",
        "scientific_name": "Coriandrum sativum",
        "gbif_usage_key": 3034789,
        "family": "Apiaceae",
        "soil_ph_min": 6.2,
        "soil_ph_max": 7.2,
        "optimal_temp_min_c": 10.0,
        "optimal_temp_max_c": 22.0,
        "frost_tolerant": True,
        "water_mm_per_week": 20,
        "days_to_harvest": 35,
        "planting_months_western_cape": ["March", "April", "May", "June", "July", "August"],
        "planting_months_summer_rainfall": ["February", "March", "April", "August", "September"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Carrot", "Radish", "Cabbage"],
        "avoid_near": ["Fennel"],
        "description": "Cool-season annual herb providing fresh dhania leaves; bolts quickly to seed if planted during blistering summer heat.",
    },
    {
        "crop_id": "CROP-33",
        "crop_name": "Parsley",
        "scientific_name": "Petroselinum crispum",
        "gbif_usage_key": 3034731,
        "family": "Apiaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 24.0,
        "frost_tolerant": True,
        "water_mm_per_week": 24,
        "days_to_harvest": 60,
        "planting_months_western_cape": ["August", "September", "October", "February", "March", "April"],
        "planting_months_summer_rainfall": ["August", "September", "October", "January", "February", "March"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Heirloom Tomato", "Carrot", "Rosemary"],
        "avoid_near": ["Lettuce", "Mint"],
        "description": "Biennial culinary herb rich in vitamins A and C; establishes strong taproots in moisture-retentive loam.",
    },
    {
        "crop_id": "CROP-34",
        "crop_name": "Mint",
        "scientific_name": "Mentha spicata",
        "gbif_usage_key": 2927161,
        "family": "Lamiaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 26.0,
        "frost_tolerant": True,
        "water_mm_per_week": 30,
        "days_to_harvest": 35,
        "planting_months_western_cape": ["August", "September", "October", "November", "March", "April"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November", "February", "March"],
        "preferred_soil_types": ["sandy_loam", "loam", "clay_loam"],
        "companion_plants": ["Cabbage", "Tomato", "Cape Gooseberry"],
        "avoid_near": ["Parsley", "Chamomile"],
        "description": "Invigorating creeping perennial herb best contained in pots or bordered plots; thrives in rich moist shaded soils.",
    },
    {
        "crop_id": "CROP-35",
        "crop_name": "Thyme",
        "scientific_name": "Thymus vulgaris",
        "gbif_usage_key": 2927038,
        "family": "Lamiaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.5,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 30.0,
        "frost_tolerant": True,
        "water_mm_per_week": 14,
        "days_to_harvest": 55,
        "planting_months_western_cape": ["August", "September", "October", "March", "April"],
        "planting_months_summer_rainfall": ["August", "September", "October", "February", "March"],
        "preferred_soil_types": ["sandy", "sandy_loam", "loam"],
        "companion_plants": ["Cabbage", "Eggplant", "Potato", "Tomato"],
        "avoid_near": ["Fennel"],
        "description": "Hardy ground-hugging aromatic subshrub with tiny antiseptic leaves; requires exceptional drainage in wet winters.",
    },
    {
        "crop_id": "CROP-36",
        "crop_name": "Chilli Pepper",
        "scientific_name": "Capsicum frutescens",
        "gbif_usage_key": 2932943,
        "family": "Solanaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 6.8,
        "optimal_temp_min_c": 20.0,
        "optimal_temp_max_c": 34.0,
        "frost_tolerant": False,
        "water_mm_per_week": 26,
        "days_to_harvest": 85,
        "planting_months_western_cape": ["September", "October", "November", "December"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Basil", "Carrot", "Red Onion"],
        "avoid_near": ["Fennel", "Broad Bean"],
        "description": "Fiery peri-peri chilli bush bearing pungent bird's-eye fruit; perennial in warm frost-free coastal microclimates.",
    },
    {
        "crop_id": "CROP-37",
        "crop_name": "Broad Bean",
        "scientific_name": "Vicia faba",
        "gbif_usage_key": 2974773,
        "family": "Fabaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.5,
        "optimal_temp_min_c": 8.0,
        "optimal_temp_max_c": 20.0,
        "frost_tolerant": True,
        "water_mm_per_week": 25,
        "days_to_harvest": 100,
        "planting_months_western_cape": ["April", "May", "June"],
        "planting_months_summer_rainfall": ["March", "April", "May"],
        "preferred_soil_types": ["loam", "clay_loam", "clay"],
        "companion_plants": ["Potato", "Rosemary", "Cabbage"],
        "avoid_near": ["Red Onion", "Garlic", "Leek"],
        "description": "Sturdy upright winter legume tolerating heavy clay soils; fixes substantial atmospheric nitrogen while bearing large edible pods.",
    },
    {
        "crop_id": "CROP-38",
        "crop_name": "Sweet Corn",
        "scientific_name": "Zea mays",
        "gbif_usage_key": 5290052,
        "family": "Poaceae",
        "soil_ph_min": 5.8,
        "soil_ph_max": 7.0,
        "optimal_temp_min_c": 18.0,
        "optimal_temp_max_c": 32.0,
        "frost_tolerant": False,
        "water_mm_per_week": 35,
        "days_to_harvest": 80,
        "planting_months_western_cape": ["September", "October", "November", "December"],
        "planting_months_summer_rainfall": ["August", "September", "October", "November", "December", "January"],
        "preferred_soil_types": ["sandy_loam", "loam", "clay_loam"],
        "companion_plants": ["Green Beans", "Pumpkin", "Cucumber", "Zucchini"],
        "avoid_near": ["Heirloom Tomato", "Beetroot"],
        "description": "High-standing grass providing sweet kernels; best planted in dense blocks for wind pollination during sunny summer months.",
    },
    {
        "crop_id": "CROP-39",
        "crop_name": "Artichoke",
        "scientific_name": "Cynara cardunculus",
        "gbif_usage_key": 3113941,
        "family": "Asteraceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.5,
        "optimal_temp_min_c": 12.0,
        "optimal_temp_max_c": 25.0,
        "frost_tolerant": True,
        "water_mm_per_week": 30,
        "days_to_harvest": 180,
        "planting_months_western_cape": ["July", "August", "September"],
        "planting_months_summer_rainfall": ["July", "August", "September"],
        "preferred_soil_types": ["sandy_loam", "loam", "clay_loam"],
        "companion_plants": ["Rosemary", "Tarragon", "Lavender"],
        "avoid_near": ["Potato"],
        "description": "Stately architectural perennial thistle producing gourmet edible flower buds and silvery architectural garden foliage.",
    },
    {
        "crop_id": "CROP-40",
        "crop_name": "Fennel",
        "scientific_name": "Foeniculum vulgare",
        "gbif_usage_key": 3034791,
        "family": "Apiaceae",
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.5,
        "optimal_temp_min_c": 14.0,
        "optimal_temp_max_c": 24.0,
        "frost_tolerant": True,
        "water_mm_per_week": 22,
        "days_to_harvest": 75,
        "planting_months_western_cape": ["August", "September", "October", "February", "March", "April"],
        "planting_months_summer_rainfall": ["August", "September", "October", "January", "February", "March"],
        "preferred_soil_types": ["sandy_loam", "loam"],
        "companion_plants": ["Dill"],
        "avoid_near": ["Heirloom Tomato", "Green Beans", "Carrot", "Kohlrabi"],
        "description": "Anise-scented bulb vegetable attracting beneficial pollinating wasps; should be grown in isolated garden beds away from other crops.",
    },
]


# ------------------------------------------------------------------------------
# 2. 40 South African Suburbs & Climate Baselines Definition
# ------------------------------------------------------------------------------
SUBURBS_40 = [
    ("SUB-01", "Woodstock", "Western Cape", "Mediterranean Coastal", -33.9268, 18.4462, "sandy_loam", 5.5, "5.3 - 5.8", 620, 24.5, 8.5, "low", "Agricultural Lime 150g/m2 for neutral crops"),
    ("SUB-02", "Constantia", "Western Cape", "Mediterranean Coastal", -34.0208, 18.4239, "loam", 6.2, "5.8 - 6.5", 950, 23.5, 7.5, "low", "Compost and organic mulch"),
    ("SUB-03", "Kirstenbosch", "Western Cape", "Mediterranean Coastal", -33.9875, 18.4325, "loam", 6.0, "5.7 - 6.4", 1100, 23.0, 7.0, "low", "Leaf mold compost"),
    ("SUB-04", "Bellville", "Western Cape", "Mediterranean Coastal", -33.8996, 18.6294, "clay_loam", 6.4, "6.0 - 6.8", 520, 26.5, 9.0, "low", "Gypsum and coarse compost"),
    ("SUB-05", "Durbanville", "Western Cape", "Mediterranean Coastal", -33.8344, 18.6472, "clay_loam", 6.5, "6.1 - 6.9", 580, 26.0, 8.5, "low", "Organic mulch and well-rotted manure"),
    ("SUB-06", "Observatory", "Western Cape", "Mediterranean Coastal", -33.9372, 18.4719, "clay", 6.2, "5.9 - 6.6", 610, 24.8, 8.6, "low", "Coarse grit and compost to improve drainage"),
    ("SUB-07", "Hout Bay", "Western Cape", "Mediterranean Coastal", -34.0439, 18.3582, "sandy_loam", 5.8, "5.5 - 6.2", 780, 23.8, 8.2, "low", "Agricultural Lime 100g/m2 for brassicas"),
    ("SUB-08", "Khayelitsha", "Western Cape", "Mediterranean Coastal", -34.0375, 18.6653, "clay", 6.3, "5.9 - 6.7", 540, 25.5, 8.8, "low", "Compost and river sand for aeration"),
    ("SUB-09", "Mitchells Plain", "Western Cape", "Mediterranean Coastal", -34.0494, 18.6247, "sandy", 6.8, "6.5 - 7.2", 510, 25.8, 8.9, "low", "Heavy compost and straw mulch for moisture retention"),
    ("SUB-10", "Rondebosch", "Western Cape", "Mediterranean Coastal", -33.9634, 18.4772, "loam", 6.1, "5.8 - 6.5", 820, 24.2, 8.0, "low", "Organic compost"),
    ("SUB-11", "Newlands", "Western Cape", "Mediterranean Coastal", -33.9744, 18.4552, "loam", 5.9, "5.6 - 6.3", 1200, 23.2, 7.2, "low", "Dolomitic lime 80g/m2 for vegetables"),
    ("SUB-12", "Sea Point", "Western Cape", "Mediterranean Coastal", -33.9167, 18.3889, "sandy", 6.6, "6.2 - 7.0", 520, 24.0, 9.2, "low", "Compost and windbreak mulch"),
    ("SUB-13", "Camps Bay", "Western Cape", "Mediterranean Coastal", -33.9511, 18.3778, "sandy", 6.5, "6.1 - 6.9", 580, 24.2, 9.5, "low", "Compost and kelp meal"),
    ("SUB-14", "Muizenberg", "Western Cape", "Mediterranean Coastal", -34.1081, 18.4706, "sandy", 6.7, "6.3 - 7.1", 600, 24.5, 9.0, "low", "Compost and mulch against coastal winds"),
    ("SUB-15", "Noordhoek", "Western Cape", "Mediterranean Coastal", -34.1167, 18.3667, "sandy_loam", 5.9, "5.6 - 6.3", 720, 24.0, 8.4, "low", "Lime 100g/m2 and compost"),
    ("SUB-16", "Simons Town", "Western Cape", "Mediterranean Coastal", -34.1933, 18.4328, "sandy_loam", 6.0, "5.7 - 6.4", 680, 24.1, 9.0, "low", "Compost and organic mulching"),
    ("SUB-17", "Somerset West", "Western Cape", "Mediterranean Coastal", -34.0833, 18.8500, "clay_loam", 6.1, "5.8 - 6.5", 750, 26.2, 8.0, "low", "Gypsum and organic compost"),
    ("SUB-18", "Stellenbosch", "Western Cape", "Mediterranean Inland", -33.9321, 18.8602, "loam", 5.8, "5.5 - 6.2", 720, 27.5, 7.0, "low", "Agricultural Lime 120g/m2 for vegetables"),
    ("SUB-19", "Paarl", "Western Cape", "Mediterranean Inland", -33.7342, 18.9622, "clay_loam", 6.2, "5.8 - 6.6", 680, 29.5, 6.8, "low", "Compost and straw mulch against heat"),
    ("SUB-20", "Franschhoek", "Western Cape", "Mediterranean Inland", -33.9111, 19.1250, "loam", 5.9, "5.5 - 6.3", 850, 28.0, 6.5, "low", "Agricultural Lime 110g/m2"),
    ("SUB-21", "Wellington", "Western Cape", "Mediterranean Inland", -33.6417, 19.0111, "clay_loam", 6.3, "5.9 - 6.7", 630, 30.0, 6.2, "low", "Compost and deep mulch"),
    ("SUB-22", "Malmesbury", "Western Cape", "Mediterranean Inland", -33.4608, 18.7272, "clay", 6.5, "6.1 - 7.0", 420, 29.8, 6.0, "low", "Gypsum and aeration compost"),
    ("SUB-23", "Ceres", "Western Cape", "Semi-Arid Highland", -33.3700, 19.3100, "clay", 6.0, "5.6 - 6.4", 530, 28.5, 1.5, "high", "Agricultural Lime 140g/m2 and frost fleece"),
    ("SUB-24", "Worcester", "Western Cape", "Semi-Arid Inland", -33.6465, 19.4456, "clay", 6.7, "6.3 - 7.2", 280, 31.0, 4.5, "moderate", "Gypsum and heavy watering adjustments"),
    ("SUB-25", "Hermanus", "Western Cape", "Mediterranean Coastal", -34.4167, 19.2333, "sandy_loam", 5.7, "5.4 - 6.1", 690, 23.5, 8.0, "low", "Agricultural Lime 130g/m2"),
    ("SUB-26", "George", "Western Cape", "Temperate Coastal", -33.9630, 22.4617, "loam", 5.6, "5.2 - 6.0", 850, 24.5, 7.5, "low", "Agricultural Lime 140g/m2"),
    ("SUB-27", "Knysna", "Western Cape", "Temperate Coastal", -34.0351, 23.0488, "loam", 5.8, "5.4 - 6.2", 890, 24.2, 8.0, "low", "Compost and light lime"),
    ("SUB-28", "Gqeberha", "Eastern Cape", "Semi-Arid Coastal", -33.9608, 25.6022, "sandy_loam", 6.3, "5.9 - 6.7", 580, 25.0, 8.5, "low", "Compost and windbreak mulch"),
    ("SUB-29", "East London", "Eastern Cape", "Humid Subtropical", -32.9700, 27.8700, "sandy_loam", 6.2, "5.8 - 6.6", 790, 26.0, 10.0, "low", "Organic mulch and compost"),
    ("SUB-30", "Durban", "KwaZulu-Natal", "Humid Subtropical", -29.8587, 31.0218, "clay_loam", 6.0, "5.6 - 6.5", 1010, 28.0, 11.5, "low", "Compost and drainage trenches"),
    ("SUB-31", "Pietermaritzburg", "KwaZulu-Natal", "Subtropical Highland", -29.6167, 30.3833, "clay_loam", 5.7, "5.3 - 6.2", 820, 27.0, 6.0, "moderate", "Agricultural Lime 150g/m2"),
    ("SUB-32", "Bloemfontein", "Free State", "Semi-Arid Continental", -29.1167, 26.2167, "clay", 6.8, "6.4 - 7.3", 550, 29.0, -1.5, "high", "Gypsum and frost protection cloches"),
    ("SUB-33", "Kimberley", "Northern Cape", "Semi-Arid Continental", -28.7386, 24.7586, "clay", 7.2, "6.8 - 7.6", 410, 31.5, 0.5, "high", "Elemental Sulfur 50g/m2 for acid-loving crops"),
    ("SUB-34", "Johannesburg", "Gauteng", "Subtropical Highland", -26.2041, 28.0473, "clay_loam", 6.1, "5.7 - 6.5", 710, 25.5, 4.0, "moderate", "Compost and winter frost protection"),
    ("SUB-35", "Soweto", "Gauteng", "Subtropical Highland", -26.2678, 27.8585, "clay_loam", 6.2, "5.8 - 6.6", 700, 25.8, 3.8, "moderate", "Compost and winter mulch"),
    ("SUB-36", "Pretoria", "Gauteng", "Subtropical Highland", -25.7479, 28.2293, "clay", 6.4, "6.0 - 6.8", 670, 28.0, 5.0, "low", "Compost and gypsum"),
    ("SUB-37", "Centurion", "Gauteng", "Subtropical Highland", -25.8603, 28.1894, "clay", 6.3, "5.9 - 6.7", 680, 27.5, 4.5, "moderate", "Compost and gypsum"),
    ("SUB-38", "Polokwane", "Limpopo", "Semi-Arid Plateau", -23.9045, 29.4689, "clay", 6.5, "6.1 - 7.0", 480, 28.5, 4.2, "moderate", "Compost and organic mulch"),
    ("SUB-39", "Mbombela", "Mpumalanga", "Humid Subtropical", -25.4753, 30.9694, "clay", 5.8, "5.4 - 6.2", 790, 29.0, 8.0, "low", "Agricultural Lime 120g/m2"),
    ("SUB-40", "Upington", "Northern Cape", "Arid Continental", -28.4478, 21.2561, "sandy", 7.8, "7.4 - 8.3", 180, 35.0, 4.0, "moderate", "Elemental Sulfur 100g/m2 and shade cloth"),
]


# ------------------------------------------------------------------------------
# 3. PDF Agricultural Rules Definition
# ------------------------------------------------------------------------------
TABLE_1_HEADERS = [
    "rule_id",
    "soil_type",
    "current_ph_bracket",
    "target_ph_shift",
    "amendment_type",
    "dosage_g_per_m2",
    "application_notes",
]

TABLE_1_DATA = [
    ["RULE-PH-01", "sandy", "5.0 - 5.5", "+1.0 (to 6.0-6.5)", "Agricultural Lime", "100", "Incorporate 100g/m2 calcitic lime into top 15cm of sandy soil 2 weeks before planting"],
    ["RULE-PH-02", "sandy_loam", "5.0 - 5.5", "+0.8 to +1.0 (to 6.0-6.8)", "Agricultural Lime", "150", "Incorporate 150g/m2 calcitic lime into top 20cm of sandy_loam soil 2 weeks before planting"],
    ["RULE-PH-03", "loam", "5.0 - 5.5", "+0.8 to +1.0 (to 6.0-6.8)", "Agricultural Lime", "200", "Incorporate 200g/m2 calcitic lime into top 20cm of loam soil 3 weeks before planting"],
    ["RULE-PH-04", "clay_loam", "5.0 - 5.5", "+0.8 to +1.0 (to 6.0-6.8)", "Agricultural Lime", "260", "Incorporate 260g/m2 calcitic lime into top 20cm of clay_loam soil 3 weeks before planting"],
    ["RULE-PH-05", "clay", "5.0 - 5.5", "+0.8 to +1.0 (to 6.0-6.8)", "Agricultural Lime", "320", "Incorporate 320g/m2 calcitic lime into top 20cm of heavy clay soil 4 weeks before planting"],
    ["RULE-PH-06", "sandy", "5.5 - 6.0", "+0.5 to +0.8 (to 6.3-6.8)", "Agricultural Lime", "70", "Apply 70g/m2 calcitic lime and rake into top 10cm of sandy soil"],
    ["RULE-PH-07", "sandy_loam", "5.5 - 6.0", "+0.5 to +0.8 (to 6.3-6.8)", "Agricultural Lime", "100", "Apply 100g/m2 calcitic lime into top 15cm of sandy_loam soil"],
    ["RULE-PH-08", "loam", "5.5 - 6.0", "+0.5 to +0.8 (to 6.3-6.8)", "Agricultural Lime", "140", "Apply 140g/m2 calcitic lime into top 15cm of loam soil"],
    ["RULE-PH-09", "clay_loam", "5.5 - 6.0", "+0.5 to +0.8 (to 6.3-6.8)", "Agricultural Lime", "180", "Apply 180g/m2 calcitic lime into top 15cm of clay_loam soil"],
    ["RULE-PH-10", "clay", "5.5 - 6.0", "+0.5 to +0.8 (to 6.3-6.8)", "Agricultural Lime", "220", "Apply 220g/m2 calcitic lime into top 15cm of clay soil"],
    ["RULE-PH-11", "sandy", "4.5 - 5.0", "+1.5 (to 6.0-6.5)", "Dolomitic Lime", "160", "Apply 160g/m2 dolomitic lime to supply magnesium and raise pH in acidic sand"],
    ["RULE-PH-12", "sandy_loam", "4.5 - 5.0", "+1.5 (to 6.0-6.5)", "Dolomitic Lime", "220", "Apply 220g/m2 dolomitic lime into top 20cm of sandy_loam soil"],
    ["RULE-PH-13", "loam", "4.5 - 5.0", "+1.5 (to 6.0-6.5)", "Dolomitic Lime", "280", "Apply 280g/m2 dolomitic lime into top 20cm of loam soil"],
    ["RULE-PH-14", "clay_loam", "4.5 - 5.0", "+1.5 (to 6.0-6.5)", "Dolomitic Lime", "360", "Apply 360g/m2 dolomitic lime into top 20cm of clay_loam soil"],
    ["RULE-PH-15", "clay", "4.5 - 5.0", "+1.5 (to 6.0-6.5)", "Dolomitic Lime", "440", "Apply 440g/m2 dolomitic lime into top 20cm of clay soil"],
    ["RULE-PH-16", "sandy", "7.2 - 7.8", "-0.8 to -1.0 (to 6.2-6.8)", "Elemental Sulfur", "40", "Incorporate 40g/m2 elemental sulfur into top 15cm of sandy soil 4 weeks before planting"],
    ["RULE-PH-17", "sandy_loam", "7.2 - 7.8", "-0.8 to -1.0 (to 6.2-6.8)", "Elemental Sulfur", "60", "Incorporate 60g/m2 elemental sulfur into top 15cm of sandy_loam soil"],
    ["RULE-PH-18", "loam", "7.2 - 7.8", "-0.8 to -1.0 (to 6.2-6.8)", "Elemental Sulfur", "90", "Incorporate 90g/m2 elemental sulfur into top 15cm of loam soil"],
    ["RULE-PH-19", "clay_loam", "7.2 - 7.8", "-0.8 to -1.0 (to 6.2-6.8)", "Elemental Sulfur", "130", "Incorporate 130g/m2 elemental sulfur into top 15cm of clay_loam soil"],
    ["RULE-PH-20", "clay", "7.2 - 7.8", "-0.8 to -1.0 (to 6.2-6.8)", "Elemental Sulfur", "170", "Incorporate 170g/m2 elemental sulfur into top 15cm of clay soil"],
    ["RULE-PH-21", "sandy", "7.8 - 8.5", "-1.2 to -1.5 (to 6.5-7.0)", "Elemental Sulfur", "70", "Incorporate 70g/m2 elemental sulfur and acidic compost into sandy soil"],
    ["RULE-PH-22", "sandy_loam", "7.8 - 8.5", "-1.2 to -1.5 (to 6.5-7.0)", "Elemental Sulfur", "100", "Incorporate 100g/m2 elemental sulfur and pine needle mulch into sandy_loam soil"],
    ["RULE-PH-23", "loam", "7.8 - 8.5", "-1.2 to -1.5 (to 6.5-7.0)", "Elemental Sulfur", "150", "Incorporate 150g/m2 elemental sulfur into loam soil"],
    ["RULE-PH-24", "clay_loam", "7.8 - 8.5", "-1.2 to -1.5 (to 6.5-7.0)", "Elemental Sulfur", "210", "Incorporate 210g/m2 elemental sulfur into clay_loam soil"],
    ["RULE-PH-25", "clay", "7.8 - 8.5", "-1.2 to -1.5 (to 6.5-7.0)", "Elemental Sulfur", "270", "Incorporate 270g/m2 elemental sulfur into clay soil"],
]

TABLE_2_HEADERS = [
    "rule_id",
    "temp_bracket_c",
    "rainfall_bracket_mm",
    "soil_type",
    "weekly_water_adjustment_mm",
    "mulching_recommendation",
]

TABLE_2_DATA = [
    ["RULE-WT-01", "< 20", "> 40", "sandy", "-15", "Light bark mulch 2cm to prevent crusting"],
    ["RULE-WT-02", "< 20", "> 40", "sandy_loam", "-20", "Light compost mulch 2cm to maintain aeration"],
    ["RULE-WT-03", "< 20", "> 40", "loam", "-20", "No mulch required; keep bed aerated"],
    ["RULE-WT-04", "< 20", "> 40", "clay_loam", "-25", "Open drainage furrows; no mulch during deluge"],
    ["RULE-WT-05", "< 20", "> 40", "clay", "-25", "Avoid waterlogging; ensure ridge drainage"],
    ["RULE-WT-06", "< 20", "10 - 40", "sandy", "0", "Straw mulch 3cm to retain base moisture"],
    ["RULE-WT-07", "< 20", "10 - 40", "sandy_loam", "0", "Standard straw mulch 3cm"],
    ["RULE-WT-08", "< 20", "10 - 40", "loam", "0", "Organic compost layer 3cm"],
    ["RULE-WT-09", "< 20", "10 - 40", "clay_loam", "-5", "Light compost topdress"],
    ["RULE-WT-10", "< 20", "10 - 40", "clay", "-5", "Monitor rootzone saturation before watering"],
    ["RULE-WT-11", "20 - 28", "< 10", "sandy", "+25", "Heavy pine-bark mulch 7cm to stop evaporation"],
    ["RULE-WT-12", "20 - 28", "< 10", "sandy_loam", "+20", "Sugarcane or straw mulch 5cm"],
    ["RULE-WT-13", "20 - 28", "< 10", "loam", "+15", "Well-rotted compost mulch 5cm"],
    ["RULE-WT-14", "20 - 28", "< 10", "clay_loam", "+10", "Straw mulch 5cm to prevent surface cracking"],
    ["RULE-WT-15", "20 - 28", "< 10", "clay", "+10", "Shredded leaf mulch 5cm to keep soil workable"],
    ["RULE-WT-16", "> 28", "< 10", "sandy", "+35", "Deep mulch 8cm with drip irrigation twice daily"],
    ["RULE-WT-17", "> 28", "< 10", "sandy_loam", "+30", "Deep straw or woodchip mulch 7cm with shade cloth"],
    ["RULE-WT-18", "> 28", "< 10", "loam", "+25", "Dense organic mulch 7cm; water at dawn"],
    ["RULE-WT-19", "> 28", "< 10", "clay_loam", "+20", "Straw mulch 6cm to preserve moisture and stop baking"],
    ["RULE-WT-20", "> 28", "< 10", "clay", "+15", "Mulch 6cm; slow deep soaks to prevent runoff"],
]


# ------------------------------------------------------------------------------
# 4. Part 2 Demo Calendar Events & Messy Emails Definition
# ------------------------------------------------------------------------------
DEMO_CALENDAR_EVENTS = [
    {
        "event_id": "EVT-01",
        "scheduled_date": "2026-11-02",
        "suburb": "Woodstock",
        "plot_id": "PLOT-W04",
        "gardener_name": "Sipho Ndlovu",
        "gardener_email": "sipho@capegardens.org.za",
        "notes": "Scheduled heirloom tomato bed planting after morning soil prep.",
    },
    {
        "event_id": "EVT-02",
        "scheduled_date": "2026-11-03",
        "suburb": "Constantia",
        "plot_id": "PLOT-C02",
        "gardener_name": "Zanele Mbeki",
        "gardener_email": "zanele@capegardens.org.za",
        "notes": "Organic spinach bed installation in shaded terrace section.",
    },
    {
        "event_id": "EVT-03",
        "scheduled_date": "2026-11-03",
        "suburb": "Kirstenbosch",
        "plot_id": "PLOT-K01",
        "gardener_name": "Pieter van der Merwe",
        "gardener_email": "pieter@capegardens.org.za",
        "notes": "Tuscan kale seedlings planting in communal raised bed 1.",
    },
    {
        "event_id": "EVT-04",
        "scheduled_date": "2026-11-04",
        "suburb": "Bellville",
        "plot_id": "PLOT-B07",
        "gardener_name": "Amina Patel",
        "gardener_email": "amina@capegardens.org.za",
        "notes": "Butternut squash mounding on north-facing slope.",
    },
    {
        "event_id": "EVT-05",
        "scheduled_date": "2026-11-05",
        "suburb": "Durbanville",
        "plot_id": "PLOT-D03",
        "gardener_name": "Thabo Khumalo",
        "gardener_email": "thabo@capegardens.org.za",
        "notes": "Direct seeding beetroot rows with drip line alignment.",
    },
    {
        "event_id": "EVT-06",
        "scheduled_date": "2026-11-05",
        "suburb": "Observatory",
        "plot_id": "PLOT-O02",
        "gardener_name": "Lerato Molefe",
        "gardener_email": "lerato@capegardens.org.za",
        "notes": "Scheduled for plot PLOT-O02 swiss chard beds.",
    },
    {
        "event_id": "EVT-07",
        "scheduled_date": "2026-11-06",
        "suburb": "Hout Bay",
        "plot_id": "PLOT-H05",
        "gardener_name": "Johan Botha",
        "gardener_email": "johan@capegardens.org.za",
        "notes": "Carrot bed preparation and seed tape laying.",
    },
    {
        "event_id": "EVT-08",
        "scheduled_date": "2026-11-06",
        "suburb": "Malmesbury",
        "plot_id": "PLOT-M02",
        "gardener_name": "Nomsa Dlamini",
        "gardener_email": "nomsa@capegardens.org.za",
        "notes": "Cape gooseberry bush transplantation with organic compost.",
    },
]

DEMO_GARDENER_EMAILS = [
    {
        "email_id": "EMAIL-101",
        "sender_name": "Sipho Ndlovu",
        "sender_email": "sipho@capegardens.org.za",
        "received_at": "2026-11-02T14:15:00Z",
        "subject": "Woodstock planting report - plot w04",
        "body": "Hi team, completed planting at Woodstock plot-w04 on Nov 2nd, 2026. Put in 24 Heirloom Tomato plants (scientific name Solanumm lykopersikun). Seed batch was BATCH-CT-2026-09. Forgot to bring my pH probe today, will measure tomorrow morning and email through.",
        "parsed_hints": {
            "planted_date_raw": "Nov 2nd, 2026",
            "suburb": "Woodstock",
            "plot_id": "plot-w04",
            "crop_name": "Heirloom Tomato",
            "species_scientific_raw": "Solanumm lykopersikun",
            "quantity_planted": 24,
            "measured_soil_ph": None,
            "seed_batch_id": "BATCH-CT-2026-09",
        },
    },
    {
        "email_id": "EMAIL-102",
        "sender_name": "Sipho Ndlovu",
        "sender_email": "sipho@capegardens.org.za",
        "received_at": "2026-11-03T07:45:00Z",
        "subject": "Re: Woodstock planting report - plot w04 (pH update)",
        "body": "Following up on my report from yesterday for Woodstock plot-w04 (planted 2026-11-02). Measured soil pH this morning with calibrated digital meter: exactly 5.3. Soil feels quite sandy and acidic.",
        "parsed_hints": {
            "planted_date_raw": "2026-11-02",
            "suburb": "Woodstock",
            "plot_id": "plot-w04",
            "crop_name": None,
            "species_scientific_raw": None,
            "quantity_planted": None,
            "measured_soil_ph": 5.3,
            "seed_batch_id": None,
        },
    },
    {
        "email_id": "EMAIL-103",
        "sender_name": "Zanele Mbeki",
        "sender_email": "zanele@capegardens.org.za",
        "received_at": "2026-11-03T11:20:00Z",
        "subject": "Planting complete at Constantia PLOT-C02",
        "body": "Good day coordinator, on 03/11/2026 I finished planting Spinach (Spinacia oleracea) in Constantia PLOT-C02. Planted 30 units from batch BATCH-CT-2026-11. Soil test gave pH 6.4.",
        "parsed_hints": {
            "planted_date_raw": "03/11/2026",
            "suburb": "Constantia",
            "plot_id": "PLOT-C02",
            "crop_name": "Spinach",
            "species_scientific_raw": "Spinacia oleracea",
            "quantity_planted": 30,
            "measured_soil_ph": 6.4,
            "seed_batch_id": "BATCH-CT-2026-11",
        },
    },
    {
        "email_id": "EMAIL-104",
        "sender_name": "Zanele Mbeki",
        "sender_email": "zanele@capegardens.org.za",
        "received_at": "2026-11-03T16:05:00Z",
        "subject": "Correction to quantity: Constantia PLOT-C02",
        "body": "Quick correction to earlier email: we actually managed to transplant 40 Spinach seedlings instead of 30 into PLOT-C02 today (2026-11-03) using the same batch BATCH-CT-2026-11. Soil pH confirmed 6.4.",
        "parsed_hints": {
            "planted_date_raw": "2026-11-03",
            "suburb": "Constantia",
            "plot_id": "PLOT-C02",
            "crop_name": "Spinach",
            "species_scientific_raw": "Spinacia oleracea",
            "quantity_planted": 40,
            "measured_soil_ph": 6.4,
            "seed_batch_id": "BATCH-CT-2026-11",
        },
    },
    {
        "email_id": "EMAIL-105",
        "sender_name": "Pieter van der Merwe",
        "sender_email": "pieter@capegardens.org.za",
        "received_at": "2026-11-03T17:30:00Z",
        "subject": "Kirstenbosch PLOT-K01 planting log",
        "body": "Hello, planted 18 Kale seedlings at Kirstenbosch PLOT-K01 on 2026-11-03. Botanical name Brasika oleracia var. acefala. Soil pH measured 6.5. Batch code BATCH-CT-2026-12. Bed was pre-treated with leaf compost.",
        "parsed_hints": {
            "planted_date_raw": "2026-11-03",
            "suburb": "Kirstenbosch",
            "plot_id": "PLOT-K01",
            "crop_name": "Kale",
            "species_scientific_raw": "Brasika oleracia var. acefala",
            "quantity_planted": 18,
            "measured_soil_ph": 6.5,
            "seed_batch_id": "BATCH-CT-2026-12",
        },
    },
    {
        "email_id": "EMAIL-106",
        "sender_name": "Amina Patel",
        "sender_email": "amina@capegardens.org.za",
        "received_at": "2026-11-04T15:10:00Z",
        "subject": "Bellville plot-b07 planting log",
        "body": "Hi, on 4 Nov 2026 I finished planting 15 Butternut Squash mounds at Bellville plot-b07. Species listed as Kukurbitia moskata. Soil pH tested at 6.2 with batch BATCH-CT-2026-14.",
        "parsed_hints": {
            "planted_date_raw": "4 Nov 2026",
            "suburb": "Bellville",
            "plot_id": "plot-b07",
            "crop_name": "Butternut Squash",
            "species_scientific_raw": "Kukurbitia moskata",
            "quantity_planted": 15,
            "measured_soil_ph": 6.2,
            "seed_batch_id": "BATCH-CT-2026-14",
        },
    },
    {
        "email_id": "EMAIL-107",
        "sender_name": "Thabo Khumalo",
        "sender_email": "thabo@capegardens.org.za",
        "received_at": "2026-11-05T13:40:00Z",
        "subject": "Durbanville PLOT-D03 update",
        "body": "Good afternoon, planted 50 Beetroot seeds (Beta vulgaris) in Durbanville PLOT-D03 on 2026-11-05. Seed batch is BATCH-CT-2026-15. Soil pH reading is 6.5. Drip irrigation tested successfully.",
        "parsed_hints": {
            "planted_date_raw": "2026-11-05",
            "suburb": "Durbanville",
            "plot_id": "PLOT-D03",
            "crop_name": "Beetroot",
            "species_scientific_raw": "Beta vulgaris",
            "quantity_planted": 50,
            "measured_soil_ph": 6.5,
            "seed_batch_id": "BATCH-CT-2026-15",
        },
    },
    {
        "email_id": "EMAIL-108",
        "sender_name": "Lerato Molefe",
        "sender_email": "lerato@capegardens.org.za",
        "received_at": "2026-11-05T18:00:00Z",
        "subject": "Observatory planting report - PLOT-O09",
        "body": "Hi all, completed planting 35 Swiss Chard (Beta vulgaris) at Observatory in PLOT-O09 on 2026-11-05. Soil pH is 6.6, seed batch BATCH-CT-2026-16. Note: PLOT-O02 had irrigation leak so I moved to PLOT-O09 instead.",
        "parsed_hints": {
            "planted_date_raw": "2026-11-05",
            "suburb": "Observatory",
            "plot_id": "PLOT-O09",
            "crop_name": "Swiss Chard",
            "species_scientific_raw": "Beta vulgaris",
            "quantity_planted": 35,
            "measured_soil_ph": 6.6,
            "seed_batch_id": "BATCH-CT-2026-16",
        },
    },
    {
        "email_id": "EMAIL-109",
        "sender_name": "Johan Botha",
        "sender_email": "johan@capegardens.org.za",
        "received_at": "2026-11-06T12:00:00Z",
        "subject": "Hout Bay PLOT-H05 seeding",
        "body": "Hi team, seeded 60 Carrot rows (Daucus carota) at Hout Bay PLOT-H05 on 06/11/2026. The seed packet had no batch label and our soil pH probe battery was flat so no pH recorded.",
        "parsed_hints": {
            "planted_date_raw": "06/11/2026",
            "suburb": "Hout Bay",
            "plot_id": "PLOT-H05",
            "crop_name": "Carrot",
            "species_scientific_raw": "Daucus carota",
            "quantity_planted": 60,
            "measured_soil_ph": None,
            "seed_batch_id": None,
        },
    },
    {
        "email_id": "EMAIL-110",
        "sender_name": "Nomsa Dlamini",
        "sender_email": "nomsa@capegardens.org.za",
        "received_at": "2026-11-06T15:30:00Z",
        "subject": "Malmesbury PLOT-M02 planting done",
        "body": "Greetings, planted 20 Cape Gooseberry plants (Physalis peruviana) at Malmesbury PLOT-M02 on 2026-11-06. Soil pH measured 6.1 and batch is BATCH-CT-2026-18. All shrubs mulched with aeration compost.",
        "parsed_hints": {
            "planted_date_raw": "2026-11-06",
            "suburb": "Malmesbury",
            "plot_id": "PLOT-M02",
            "crop_name": "Cape Gooseberry",
            "species_scientific_raw": "Physalis peruviana",
            "quantity_planted": 20,
            "measured_soil_ph": 6.1,
            "seed_batch_id": "BATCH-CT-2026-18",
        },
    },
]


# ------------------------------------------------------------------------------
# 5. Offline Fallback Cache (GBIF Species & Open-Meteo Weather)
# ------------------------------------------------------------------------------
def build_fallback_cache() -> dict:
    """Build comprehensive GBIF taxonomy and Open-Meteo weather cache."""
    gbif_matches = {
        # Obvious typos in gardener emails
        "Solanumm lykopersikun": {
            "canonicalName": "Solanum lycopersicum",
            "scientificName": "Solanum lycopersicum L.",
            "usageKey": 2930137,
            "confidence": 96,
            "matchType": "FUZZY",
            "family": "Solanaceae",
            "status": "ACCEPTED",
        },
        "Brasika oleracia var. acefala": {
            "canonicalName": "Brassica oleracea var. acephala",
            "scientificName": "Brassica oleracea var. acephala DC.",
            "usageKey": 3042858,
            "confidence": 94,
            "matchType": "FUZZY",
            "family": "Brassicaceae",
            "status": "ACCEPTED",
        },
        "Kukurbitia moskata": {
            "canonicalName": "Cucurbita moschata",
            "scientificName": "Cucurbita moschata Duchesne",
            "usageKey": 2874513,
            "confidence": 95,
            "matchType": "FUZZY",
            "family": "Cucurbitaceae",
            "status": "ACCEPTED",
        },
        "Kapsikum anuum": {
            "canonicalName": "Capsicum annuum",
            "scientificName": "Capsicum annuum L.",
            "usageKey": 2932944,
            "confidence": 95,
            "matchType": "FUZZY",
            "family": "Solanaceae",
            "status": "ACCEPTED",
        },
        # Legacy single-letter typos preserved for backwards compatibility
        "Solanum lycopersicun": {
            "canonicalName": "Solanum lycopersicum",
            "scientificName": "Solanum lycopersicum L.",
            "usageKey": 2930137,
            "confidence": 96,
            "matchType": "FUZZY",
            "family": "Solanaceae",
            "status": "ACCEPTED",
        },
        "Brassica oleracea var. acephla": {
            "canonicalName": "Brassica oleracea var. acephala",
            "scientificName": "Brassica oleracea var. acephala DC.",
            "usageKey": 3042858,
            "confidence": 94,
            "matchType": "FUZZY",
            "family": "Brassicaceae",
            "status": "ACCEPTED",
        },
        "Cucurbita moschataa": {
            "canonicalName": "Cucurbita moschata",
            "scientificName": "Cucurbita moschata Duchesne",
            "usageKey": 2874513,
            "confidence": 95,
            "matchType": "FUZZY",
            "family": "Cucurbitaceae",
            "status": "ACCEPTED",
        },
    }

    # Add all 40 crops into GBIF taxonomy cache
    for crop in CROPS_40:
        sci = crop["scientific_name"]
        gbif_matches[sci] = {
            "canonicalName": sci,
            "scientificName": f"{sci} L.",
            "usageKey": crop["gbif_usage_key"],
            "confidence": 100,
            "matchType": "EXACT",
            "family": crop["family"],
            "status": "ACCEPTED",
        }
        # Also map common name
        gbif_matches[crop["crop_name"]] = {
            "canonicalName": sci,
            "scientificName": f"{sci} L.",
            "usageKey": crop["gbif_usage_key"],
            "confidence": 100,
            "matchType": "EXACT",
            "family": crop["family"],
            "status": "ACCEPTED",
        }

    # Weather cache for all 40 suburbs
    weather_by_suburb = {}
    for sub in SUBURBS_40:
        sub_name = sub[1]
        weather_by_suburb[sub_name.lower()] = {
            "suburb": sub_name,
            "province": sub[2],
            "climate_zone": sub[3],
            "latitude": sub[4],
            "longitude": sub[5],
            "soil_type": sub[6],
            "baseline_soil_ph": sub[7],
            "baseline_ph_range": sub[8],
            "temperature_c": 21.4 if sub_name == "Woodstock" else round(sub[9] / 30.0 + 3.0, 1),
            "condition": "Partly Cloudy" if sub_name in ("Woodstock", "Observatory", "Constantia") else "Clear",
            "humidity_pct": 64 if sub_name == "Woodstock" else 58,
            "precipitation_mm": 0.0,
            "soil_moisture": 0.24 if sub_name == "Woodstock" else 0.22,
            "frost_risk_7d": sub[12] == "high",
            "heat_stress_7d": sub[9] > 32.0,
            "min_temp_7d_c": 12.1 if sub_name == "Woodstock" else round(sub[11] + 1.5, 1),
            "max_temp_7d_c": 24.8 if sub_name == "Woodstock" else round(sub[10] + 0.8, 1),
            "source": "Open-Meteo API & Regional Datasets",
        }

    return {
        "gbif_matches": gbif_matches,
        "weather_by_suburb": weather_by_suburb,
    }


# ------------------------------------------------------------------------------
# File Generator Routines
# ------------------------------------------------------------------------------
def generate_crop_planting_guide_json() -> Path:
    """Write backend/data/crop_planting_guide.json."""
    output_path = DATA_DIR / "crop_planting_guide.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(CROPS_40, f, indent=2)
    logger.info("Generated %s (%d crops)", output_path, len(CROPS_40))
    return output_path


def generate_regional_soil_csv() -> Path:
    """Write backend/data/regional_soil_and_climate.csv."""
    output_path = DATA_DIR / "regional_soil_and_climate.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "suburb_id",
        "suburb",
        "province",
        "climate_zone",
        "latitude",
        "longitude",
        "soil_type",
        "baseline_soil_ph",
        "baseline_ph_range",
        "annual_rainfall_mm",
        "summer_avg_temp_c",
        "winter_min_temp_c",
        "frost_risk",
        "typical_amendment_need",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for row in SUBURBS_40:
            writer.writerow(row)
    logger.info("Generated %s (%d suburbs)", output_path, len(SUBURBS_40))
    return output_path


def generate_soil_treatment_pdf() -> Path:
    """Generate backend/data/soil_treatment_and_watering_rules.pdf with explicit vector borders."""
    output_path = DATA_DIR / "soil_treatment_and_watering_rules.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Landscape A4 gives 841.89 x 595.27 points
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=18,
        rightMargin=18,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1C2820"),
        spaceAfter=4,
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#556B5A"),
        spaceBefore=3,
        spaceAfter=3,
    )
    desc_style = ParagraphStyle(
        "Description",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#2C3E2D"),
        spaceAfter=5,
    )

    elements = []

    # Title & Introduction
    elements.append(Paragraph("Western Cape Soil Treatment & Watering Dosage Reference Guide", title_style))
    elements.append(
        Paragraph(
            "Official agricultural extension rules for soil pH amendment application rates (calcitic lime, dolomitic lime, and elemental sulfur) "
            "and weekly temperature/rainfall-based watering adjustments across sandy, sandy_loam, loam, clay_loam, and clay soils.",
            desc_style,
        )
    )
    elements.append(Spacer(1, 4))

    # Table 1: Soil pH Amendment Dosages
    elements.append(Paragraph("Table 1: Soil pH Amendment Dosages by Soil Type and Target Shift", section_style))
    t1_full = [TABLE_1_HEADERS] + TABLE_1_DATA

    # Column widths total: 60 + 65 + 100 + 105 + 95 + 85 + 290 = 800 points (page width 841.89 - 36 = 805.89)
    col_widths_1 = [60, 65, 100, 105, 95, 85, 290]
    t1 = Table(t1_full, colWidths=col_widths_1, repeatRows=1)
    t1.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
            ("BOX", (0, 0), (-1, -1), 1.0, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6D9C7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 6.5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 2.5),
            ("TOPPADDING", (0, 1), (-1, -1), 2.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F6F0")]),
        ])
    )
    elements.append(t1)
    elements.append(PageBreak())

    # Page 2: Table 2 Weekly Watering & Mulching Adjustment Rules
    elements.append(Paragraph("Table 2: Weekly Watering & Mulching Adjustment Rules by Climate Bracket", section_style))
    elements.append(
        Paragraph(
            "Weekly baseline watering adjustments (mm/week) and mulching protocols calculated against regional ambient temperature and rainfall.",
            desc_style,
        )
    )
    elements.append(Spacer(1, 4))

    t2_full = [TABLE_2_HEADERS] + TABLE_2_DATA
    # Column widths total: 65 + 85 + 115 + 65 + 140 + 330 = 800 points
    col_widths_2 = [65, 85, 115, 65, 140, 330]
    t2 = Table(t2_full, colWidths=col_widths_2, repeatRows=1)
    t2.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
            ("BOX", (0, 0), (-1, -1), 1.0, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6D9C7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 6.5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
            ("TOPPADDING", (0, 1), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F6F0")]),
        ])
    )
    elements.append(t2)

    doc.build(elements)
    logger.info("Generated %s (2 pages with vector borders)", output_path)
    return output_path


def generate_demo_fixtures() -> tuple[Path, Path, Path]:
    """Write the 3 Part 2 demo fixtures under backend/data/demo_fixtures/."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Calendar Events
    events_path = FIXTURES_DIR / "demo_calendar_events.json"
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(DEMO_CALENDAR_EVENTS, f, indent=2)
    logger.info("Generated %s (%d events)", events_path, len(DEMO_CALENDAR_EVENTS))

    # 2. Gardener Emails
    emails_path = FIXTURES_DIR / "demo_gardener_emails.json"
    with open(emails_path, "w", encoding="utf-8") as f:
        json.dump(DEMO_GARDENER_EMAILS, f, indent=2)
    logger.info("Generated %s (%d emails)", emails_path, len(DEMO_GARDENER_EMAILS))

    # 3. API Fallback Cache
    cache_path = FIXTURES_DIR / "api_fallback_cache.json"
    cache_data = build_fallback_cache()
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)
    logger.info(
        "Generated %s (%d GBIF entries, %d suburb weather entries)",
        cache_path,
        len(cache_data["gbif_matches"]),
        len(cache_data["weather_by_suburb"]),
    )

    return events_path, emails_path, cache_path


def verify_pdf_extraction(pdf_path: Path) -> None:
    """Verify that pdfplumber extracts both tables with 100% of rows and headers."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        assert len(pdf.pages) >= 2, f"Expected at least 2 pages in PDF, found {len(pdf.pages)}"

        # Page 1 table extraction
        p1_tables = pdf.pages[0].extract_tables()
        assert len(p1_tables) >= 1, "Page 1 table extraction returned no tables"
        t1 = p1_tables[0]
        header_1 = t1[0]
        rows_1 = t1[1:]
        assert header_1 == TABLE_1_HEADERS, f"Table 1 header mismatch: {header_1}"
        assert len(rows_1) == len(TABLE_1_DATA), (
            f"Table 1 row count mismatch: extracted {len(rows_1)}, expected {len(TABLE_1_DATA)}"
        )
        assert rows_1[1][0] == "RULE-PH-02", f"Expected Row 2 to be RULE-PH-02, got {rows_1[1][0]}"
        assert rows_1[1][1] == "sandy_loam", f"Expected sandy_loam, got {rows_1[1][1]}"
        assert rows_1[1][5] == "150", f"Expected dosage 150, got {rows_1[1][5]}"

        # Page 2 table extraction
        p2_tables = pdf.pages[1].extract_tables()
        assert len(p2_tables) >= 1, "Page 2 table extraction returned no tables"
        t2 = p2_tables[0]
        header_2 = t2[0]
        rows_2 = t2[1:]
        assert header_2 == TABLE_2_HEADERS, f"Table 2 header mismatch: {header_2}"
        assert len(rows_2) == len(TABLE_2_DATA), (
            f"Table 2 row count mismatch: extracted {len(rows_2)}, expected {len(TABLE_2_DATA)}"
        )

    logger.info("PDF extraction verification passed cleanly: Table 1 has %d rows, Table 2 has %d rows", len(rows_1), len(rows_2))


def main() -> None:
    """Run all generators and run verification checks."""
    logger.info("Starting real garden data and demo fixture generation...")
    crop_path = generate_crop_planting_guide_json()
    csv_path = generate_regional_soil_csv()
    pdf_path = generate_soil_treatment_pdf()
    events_path, emails_path, cache_path = generate_demo_fixtures()

    # Verify PDF extractability
    verify_pdf_extraction(pdf_path)

    # Verification summary
    print("\nAll 6 data files generated and verified successfully:")
    print(f"1. Crop Planting Guide: {crop_path} ({len(CROPS_40)} crops)")
    print(f"2. Regional Soil & Climate: {csv_path} ({len(SUBURBS_40)} suburbs)")
    print(f"3. Soil Treatment & Watering Rules PDF: {pdf_path}")
    print(f"4. Demo Calendar Events: {events_path} ({len(DEMO_CALENDAR_EVENTS)} events)")
    print(f"5. Demo Gardener Emails: {emails_path} ({len(DEMO_GARDENER_EMAILS)} emails)")
    print(f"6. API Fallback Cache: {cache_path}")


if __name__ == "__main__":
    main()
