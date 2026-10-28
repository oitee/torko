import { describe, expect, it } from "vitest";
import { contrast, partyShades, shadeFor } from "../assets/js/colour.js";

// Helper to calculate hue in degrees (0..360) from a hex string.
function hexToHue(hex) {
  const clean = hex.replace("#", "");
  const num = parseInt(clean, 16);
  const r = ((num >> 16) & 255) / 255;
  const g = ((num >> 8) & 255) / 255;
  const b = (num & 255) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const d = max - min;
  if (d === 0) return 0;
  let h = 0;
  switch (max) {
    case r:
      h = (g - b) / d + (g < b ? 6 : 0);
      break;
    case g:
      h = (b - r) / d + 2;
      break;
    case b:
      h = (r - g) / d + 4;
      break;
  }
  return h * 60;
}

describe("colour utilities", () => {
  describe("contrast", () => {
    it("gives 21 for black on white and 1 for white on white", () => {
      expect(contrast("#000000", "#ffffff")).toBeCloseTo(21, 1);
      expect(contrast("#ffffff", "#ffffff")).toBeCloseTo(1, 1);
    });

    it("returns null for invalid inputs", () => {
      expect(contrast(null, "#ffffff")).toBeNull();
      expect(contrast("#000000", "")).toBeNull();
      expect(contrast("red", "#ffffff")).toBeNull();
      expect(contrast("#12", "#ffffff")).toBeNull();
    });

    it("supports 3-digit hex format", () => {
      expect(contrast("#000", "#fff")).toBeCloseTo(21, 1);
    });
  });

  describe("shadeFor", () => {
    it("adjusts #FF9933 on white to have contrast >= 3 and keeps hue within 2 degrees", () => {
      const originalHue = hexToHue("#FF9933");
      const shaded = shadeFor("#FF9933", "#ffffff", 3);
      expect(shaded).toBeTruthy();
      expect(contrast(shaded, "#ffffff")).toBeGreaterThanOrEqual(3);

      const shadedHue = hexToHue(shaded);
      const hueDiff = Math.abs(originalHue - shadedHue);
      expect(hueDiff).toBeLessThanOrEqual(2);
    });

    it("returns colour unchanged in lowercase if it already has enough contrast", () => {
      const darkColor = "#12161b";
      const result = shadeFor(darkColor, "#ffffff", 3);
      expect(result).toBe("#12161b");

      const upperColor = "#12161B";
      expect(shadeFor(upperColor, "#ffffff", 3)).toBe("#12161b");
    });

    it("returns null on null, empty string, or invalid hex", () => {
      expect(shadeFor(null, "#ffffff")).toBeNull();
      expect(shadeFor("", "#ffffff")).toBeNull();
      expect(shadeFor("red", "#ffffff")).toBeNull();
      expect(shadeFor("#ffffff", null)).toBeNull();
      expect(shadeFor("#ffffff", "blue")).toBeNull();
    });
  });

  describe("partyShades", () => {
    it("returns dark shade with contrast >= 3 on #171c22 for #22409A", () => {
      const shades = partyShades("#22409A");
      expect(shades).toBeTruthy();
      expect(shades.light).toBeTruthy();
      expect(shades.dark).toBeTruthy();

      expect(contrast(shades.light, "#ffffff")).toBeGreaterThanOrEqual(3);
      expect(contrast(shades.dark, "#171c22")).toBeGreaterThanOrEqual(3);
    });

    it("returns null for invalid inputs", () => {
      expect(partyShades(null)).toBeNull();
      expect(partyShades("")).toBeNull();
      expect(partyShades("red")).toBeNull();
    });
  });
});
