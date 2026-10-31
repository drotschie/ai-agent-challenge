// Run with: node --test frontend/tests/sourceLinks.test.mjs
// Node 26 strips TypeScript types natively, so no test framework is needed.
import { test } from "node:test";
import assert from "node:assert/strict";
import { resolveSourceTarget } from "../src/lib/sourceLinks.ts";

test("CSV row locator maps to a zero-based suburb row", () => {
  assert.deepEqual(resolveSourceTarget("regional_soil_and_climate.csv", "Row 22"), {
    subTab: "suburbs",
    rowIndex: 21,
    label: "regional_soil_and_climate.csv : Row 22",
  });
});

test("JSON locator maps to a crop name", () => {
  const target = resolveSourceTarget("crop_planting_guide.json", "Beetroot");
  assert.equal(target?.subTab, "crops");
  assert.equal(target?.cropName, "Beetroot");
});

test("PDF page 1 maps to Table 1 (soil pH rules)", () => {
  const target = resolveSourceTarget(
    "soil_treatment_and_watering_rules.pdf",
    "Page 1, Table 1, Row 5"
  );
  assert.equal(target?.subTab, "pdf_tables");
  assert.equal(target?.pdfTable, "table_1");
  assert.equal(target?.rowIndex, 4);
});

test("PDF page 2 maps to Table 2 (watering rules)", () => {
  const target = resolveSourceTarget(
    "soil_treatment_and_watering_rules.pdf",
    "Page 2, Table 1, Row 3"
  );
  assert.equal(target?.pdfTable, "table_2");
  assert.equal(target?.rowIndex, 2);
});

test("Bracketed citation labels with a file prefix still resolve", () => {
  const target = resolveSourceTarget(
    "crop_planting_guide.json",
    "[crop_planting_guide.json \u2192 Heirloom Tomato]"
  );
  assert.equal(target?.cropName, "Heirloom Tomato");

  const row = resolveSourceTarget(
    "regional_soil_and_climate.csv",
    "[regional_soil_and_climate.csv : Row 1]"
  );
  assert.equal(row?.rowIndex, 0);
});

test("Unknown files and malformed locators return null", () => {
  assert.equal(resolveSourceTarget("notes.txt", "Row 1"), null);
  assert.equal(resolveSourceTarget("regional_soil_and_climate.csv", "Row 0"), null);
  assert.equal(resolveSourceTarget("regional_soil_and_climate.csv", "Woodstock"), null);
  assert.equal(
    resolveSourceTarget("soil_treatment_and_watering_rules.pdf", "Page 3, Table 1, Row 1"),
    null
  );
  assert.equal(resolveSourceTarget("", ""), null);
});
