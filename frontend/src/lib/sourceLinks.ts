/**
 * Maps a RAG citation (source file + locator) to the exact record in the
 * Reference Data tab. Locators come from backend/app/rag/chunkers.py and are 1-based:
 *   CSV  -> "Row 22"
 *   JSON -> "Beetroot" (the crop name)
 *   PDF  -> "Page 1, Table 1, Row 5" (page 1 = soil pH rules, page 2 = watering rules)
 */

export type SourceSubTab = "crops" | "suburbs" | "pdf_tables";
export type PdfTableKey = "table_1" | "table_2";

export interface SourceTarget {
  subTab: SourceSubTab;
  pdfTable?: PdfTableKey;
  rowIndex?: number;
  cropName?: string;
  label: string;
}

export interface SourceFocus extends SourceTarget {
  /** Changes on every click so re-opening the same source scrolls again. */
  requestId: number;
}

const CROPS_FILE = "crop_planting_guide.json";
const SUBURBS_FILE = "regional_soil_and_climate.csv";
const PDF_FILE = "soil_treatment_and_watering_rules.pdf";

/** Strips surrounding brackets and any "file : " or "file -> " prefix from a citation label. */
function cleanLocator(sourceFile: string, locator: string): string {
  let text = locator.trim().replace(/^\[/, "").replace(/\]$/, "").trim();
  if (text.toLowerCase().startsWith(sourceFile.toLowerCase())) {
    text = text.slice(sourceFile.length).replace(/^\s*[^A-Za-z0-9]+\s*/, "").trim();
  }
  return text;
}

export function resolveSourceTarget(
  sourceFile: string,
  locator: string
): SourceTarget | null {
  const file = (sourceFile || "").trim().split(/[\\/]/).pop() ?? "";
  if (!file || !locator) return null;

  const clean = cleanLocator(file, locator);
  if (!clean) return null;

  if (file === SUBURBS_FILE) {
    const match = clean.match(/^Row\s+(\d+)$/i);
    if (!match) return null;
    const row = Number(match[1]);
    if (row < 1) return null;
    return { subTab: "suburbs", rowIndex: row - 1, label: `${file} : Row ${row}` };
  }

  if (file === CROPS_FILE) {
    return { subTab: "crops", cropName: clean, label: `${file} : ${clean}` };
  }

  if (file === PDF_FILE) {
    const match = clean.match(/^Page\s+(\d+),\s*Table\s+(\d+),\s*Row\s+(\d+)$/i);
    if (!match) return null;
    const page = Number(match[1]);
    const row = Number(match[3]);
    if (row < 1 || (page !== 1 && page !== 2)) return null;
    return {
      subTab: "pdf_tables",
      pdfTable: page === 1 ? "table_1" : "table_2",
      rowIndex: row - 1,
      label: `${file} : ${clean}`,
    };
  }

  return null;
}
