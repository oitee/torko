// Color utility functions for contrast calculation and party shade derivation.
// Uses WCAG 2 relative luminance formula.

// Parse a hex color string (#rgb or #rrggbb).
// Returns an object with r, g, b in 0..255 and normalized hex, or null.
function parseHex(hex) {
  if (typeof hex !== "string") {
    return null;
  }
  const clean = hex.trim();
  const match = clean.match(/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/);
  if (!match) {
    return null;
  }
  let raw = match[1];
  if (raw.length === 3) {
    raw = raw[0] + raw[0] + raw[1] + raw[1] + raw[2] + raw[2];
  }
  const num = parseInt(raw, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return { r, g, b, hex: `#${raw.toLowerCase()}` };
}

// Convert sRGB 8-bit channel to linear luminance.
function sRgbLuminance(channel) {
  const v = channel / 255;
  return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
}

// Calculate WCAG 2 relative luminance from RGB channels.
function relativeLuminance(r, g, b) {
  const R = sRgbLuminance(r);
  const G = sRgbLuminance(g);
  const B = sRgbLuminance(b);
  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

// Convert RGB channels (0..255) to HSL (h in 0..1, s in 0..1, l in 0..1).
function rgbToHsl(r, g, b) {
  const rn = r / 255;
  const gn = g / 255;
  const bn = b / 255;
  const max = Math.max(rn, gn, bn);
  const min = Math.min(rn, gn, bn);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case rn:
        h = (gn - bn) / d + (gn < bn ? 6 : 0);
        break;
      case gn:
        h = (bn - rn) / d + 2;
        break;
      case bn:
        h = (rn - gn) / d + 4;
        break;
    }
    h /= 6;
  }

  return { h, s, l };
}

// Convert HSL (h in 0..1, s in 0..1, l in 0..1) to RGB channels (0..255).
function hslToRgb(h, s, l) {
  if (s === 0) {
    const v = Math.round(l * 255);
    return { r: v, g: v, b: v };
  }

  function hue2rgb(p, q, t) {
    let val = t;
    if (val < 0) val += 1;
    if (val > 1) val -= 1;
    if (val < 1 / 6) return p + (q - p) * 6 * val;
    if (val < 1 / 2) return q;
    if (val < 2 / 3) return p + (q - p) * (2 / 3 - val) * 6;
    return p;
  }

  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  const r = Math.round(hue2rgb(p, q, h + 1 / 3) * 255);
  const g = Math.round(hue2rgb(p, q, h) * 255);
  const b = Math.round(hue2rgb(p, q, h - 1 / 3) * 255);

  return {
    r: Math.max(0, Math.min(255, r)),
    g: Math.max(0, Math.min(255, g)),
    b: Math.max(0, Math.min(255, b)),
  };
}

// Convert RGB channels (0..255) to lower-case hex string.
function rgbToHex(r, g, b) {
  const toHex = (n) => n.toString(16).padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

// Calculate the contrast ratio between two hex colours using WCAG 2.
// Returns null if either hex is invalid.
export function contrast(hexA, hexB) {
  const a = parseHex(hexA);
  const b = parseHex(hexB);
  if (!a || !b) {
    return null;
  }
  const lumA = relativeLuminance(a.r, a.g, a.b);
  const lumB = relativeLuminance(b.r, b.g, b.b);
  const l1 = Math.max(lumA, lumB);
  const l2 = Math.min(lumA, lumB);
  return (l1 + 0.05) / (l2 + 0.05);
}

// Adjust lightness of hex in HSL by 0.02 steps until contrast >= minimum against background.
// Stops when target contrast is reached.
// Returns lower-case hex string or null if hex/background is invalid.
export function shadeFor(hex, background, minimum = 3) {
  const parsedHex = parseHex(hex);
  const parsedBg = parseHex(background);
  if (!parsedHex || !parsedBg) {
    return null;
  }

  const initialContrast = contrast(parsedHex.hex, parsedBg.hex);
  if (initialContrast >= minimum) {
    return parsedHex.hex;
  }

  const bgLum = relativeLuminance(parsedBg.r, parsedBg.g, parsedBg.b);
  const isBgLight = bgLum > 0.5;
  const hsl = rgbToHsl(parsedHex.r, parsedHex.g, parsedHex.b);

  let l = hsl.l;
  let currentHex = parsedHex.hex;

  if (isBgLight) {
    while (l > 0) {
      l = Math.max(0, l - 0.02);
      const rgb = hslToRgb(hsl.h, hsl.s, l);
      currentHex = rgbToHex(rgb.r, rgb.g, rgb.b);
      if (contrast(currentHex, parsedBg.hex) >= minimum) {
        return currentHex;
      }
      if (l === 0) {
        break;
      }
    }
  } else {
    while (l < 1) {
      l = Math.min(1, l + 0.02);
      const rgb = hslToRgb(hsl.h, hsl.s, l);
      currentHex = rgbToHex(rgb.r, rgb.g, rgb.b);
      if (contrast(currentHex, parsedBg.hex) >= minimum) {
        return currentHex;
      }
      if (l === 1) {
        break;
      }
    }
  }

  return currentHex;
}

// Derive light and dark theme shades for a party colour on --sheet backgrounds.
// Returns { light, dark } or null if hex is invalid.
export function partyShades(hex) {
  const parsed = parseHex(hex);
  if (!parsed) {
    return null;
  }
  return {
    light: shadeFor(parsed.hex, "#ffffff"),
    dark: shadeFor(parsed.hex, "#171c22"),
  };
}
