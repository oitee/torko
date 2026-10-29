import { describe, expect, it } from "vitest";
import {
  SPEAKER_NOT_IDENTIFIED,
  SPEAKER_NOT_IDENTIFIED_LINE,
  countOf,
  formatDateISO,
  formatDateLong,
  formatNumber,
  ordinal,
  shareOf,
  termLong,
  termShort,
  scriptLang,
} from "../assets/js/format.js";

describe("formatNumber", () => {
  it("formats numbers with international grouping", () => {
    expect(formatNumber(1318)).toBe("1,318");
    expect(formatNumber(1234567)).toBe("1,234,567");
    expect(formatNumber(0)).toBe("0");
  });

  it("formats numeric strings with international grouping", () => {
    expect(formatNumber("1318")).toBe("1,318");
    expect(formatNumber("0")).toBe("0");
  });

  it("returns an en dash for null or undefined", () => {
    expect(formatNumber(null)).toBe("–");
    expect(formatNumber(undefined)).toBe("–");
  });

  it("returns an en dash for non-numeric values", () => {
    expect(formatNumber("abc")).toBe("–");
    expect(formatNumber("")).toBe("–");
  });
});

describe("formatDateISO", () => {
  it("returns YYYY-MM-DD format", () => {
    expect(formatDateISO("2024-03-12")).toBe("2024-03-12");
  });

  it("handles empty input", () => {
    expect(formatDateISO("")).toBe("");
    expect(formatDateISO(null)).toBe("");
  });
});

describe("formatDateLong", () => {
  it("formats dates without a leading zero on the day", () => {
    expect(formatDateLong("2024-03-12")).toBe("12 Mar 2024");
    expect(formatDateLong("2024-01-05")).toBe("5 Jan 2024");
  });

  it("handles empty input", () => {
    expect(formatDateLong("")).toBe("");
    expect(formatDateLong(null)).toBe("");
  });
});

describe("termLong", () => {
  it("adds the correct English suffix to terms", () => {
    expect(termLong(1)).toBe("1st Lok Sabha");
    expect(termLong(2)).toBe("2nd Lok Sabha");
    expect(termLong(3)).toBe("3rd Lok Sabha");
    expect(termLong(4)).toBe("4th Lok Sabha");
    expect(termLong(11)).toBe("11th Lok Sabha");
    expect(termLong(12)).toBe("12th Lok Sabha");
    expect(termLong(13)).toBe("13th Lok Sabha");
    expect(termLong(17)).toBe("17th Lok Sabha");
    expect(termLong(21)).toBe("21st Lok Sabha");
  });
});

describe("termShort", () => {
  it("formats short term names", () => {
    expect(termShort(17)).toBe("17th LS");
    expect(termShort(1)).toBe("1st LS");
  });
});

describe("ordinal", () => {
  it("adds the English ordinal ending", () => {
    expect(ordinal(1)).toBe("1st");
    expect(ordinal(2)).toBe("2nd");
    expect(ordinal(3)).toBe("3rd");
    expect(ordinal(13)).toBe("13th");
    expect(ordinal(18)).toBe("18th");
  });
});

describe("countOf", () => {
  it("formats a count out of a total with a noun", () => {
    expect(countOf(41, 1318, "speeches")).toBe("41 of 1,318 speeches");
  });

  it("formats a count without a noun", () => {
    expect(countOf(41, 1318)).toBe("41 of 1,318");
  });
});

describe("shareOf", () => {
  it("formats a share with one decimal place and counts", () => {
    expect(shareOf(41, 1318)).toBe("3.1% (41 of 1,318)");
  });

  it("returns 0 of 0 when total is 0", () => {
    expect(shareOf(0, 0)).toBe("0 of 0");
    expect(shareOf(41, 0)).toBe("0 of 0");
  });

  it("returns an en dash when n or total is missing or not a number", () => {
    expect(shareOf(null, 10)).toBe("–");
    expect(shareOf(undefined, 10)).toBe("–");
    expect(shareOf(10, null)).toBe("–");
    expect(shareOf(10, undefined)).toBe("–");
    expect(shareOf("abc", 10)).toBe("–");
    expect(shareOf(10, "abc")).toBe("–");
    expect(shareOf("", 10)).toBe("–");
  });
});

describe("constants", () => {
  it("exports exact unidentified speaker sentences", () => {
    expect(SPEAKER_NOT_IDENTIFIED).toBe("Speaker not identified");
    expect(SPEAKER_NOT_IDENTIFIED_LINE).toBe(
      "Speaker not identified. Torko could not match this name to one member."
    );
  });
});

describe("scriptLang", () => {
  it("returns hi for Devanagari text", () => {
    expect(scriptLang("माननीय अध्यक्ष")).toBe("hi");
    expect(scriptLang("Speaker माननीय")).toBe("hi");
  });

  it("returns ur for Arabic script text", () => {
    expect(scriptLang("شکریہ جناب اسپیکر")).toBe("ur");
    expect(scriptLang("Speaker شکریہ")).toBe("ur");
  });

  it("returns the language of the first script character when both exist", () => {
    expect(scriptLang("माननीय and شکریہ")).toBe("hi");
    expect(scriptLang("شکریہ and माननीय")).toBe("ur");
  });

  it("returns undefined for text with neither script", () => {
    expect(scriptLang("Plain English speech")).toBeUndefined();
    expect(scriptLang("12345 !?")).toBeUndefined();
  });

  it("returns undefined for empty or missing input", () => {
    expect(scriptLang("")).toBeUndefined();
    expect(scriptLang(null)).toBeUndefined();
    expect(scriptLang(undefined)).toBeUndefined();
  });
});
