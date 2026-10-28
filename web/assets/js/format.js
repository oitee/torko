// Fixed sentences for an unidentified speaker.
export const SPEAKER_NOT_IDENTIFIED = "Speaker not identified";
export const SPEAKER_NOT_IDENTIFIED_LINE =
  "Speaker not identified. Torko could not match this name to one member.";

// Three letter English month names.
const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

// Format a number with international grouping.
// Returns an en dash when n is null, undefined, or not a number.
export function formatNumber(n) {
  if (n === null || n === undefined || n === "") {
    return "–";
  }
  const num = Number(n);
  if (Number.isNaN(num)) {
    return "–";
  }
  return num.toLocaleString("en-US");
}

// Format a date string in ISO format (YYYY-MM-DD).
// Does not use new Date to avoid timezone shifts.
export function formatDateISO(s) {
  if (!s) {
    return "";
  }
  const parts = String(s).split("-");
  if (parts.length < 3) {
    return String(s);
  }
  const year = parts[0];
  const month = parts[1];
  const day = parts[2].slice(0, 2);
  return `${year}-${month}-${day}`;
}

// Format a date string for breadcrumbs and running text (e.g. 12 Mar 2024).
// Strips leading zeros from the day.
export function formatDateLong(s) {
  if (!s) {
    return "";
  }
  const parts = String(s).split("-");
  if (parts.length < 3) {
    return String(s);
  }
  const year = parts[0];
  const monthIndex = parseInt(parts[1], 10) - 1;
  const day = parseInt(parts[2], 10);
  const month = MONTHS[monthIndex];
  if (!month || Number.isNaN(day)) {
    return String(s);
  }
  return `${day} ${month} ${year}`;
}

// Find the English ordinal suffix for a number.
function ordinalSuffix(n) {
  const num = Math.abs(parseInt(n, 10));
  const mod100 = num % 100;
  if (mod100 >= 11 && mod100 <= 13) {
    return "th";
  }
  const mod10 = num % 10;
  if (mod10 === 1) {
    return "st";
  }
  if (mod10 === 2) {
    return "nd";
  }
  if (mod10 === 3) {
    return "rd";
  }
  return "th";
}

// Format a Lok Sabha term in full (e.g. 17th Lok Sabha).
export function termLong(n) {
  return `${n}${ordinalSuffix(n)} Lok Sabha`;
}

// Format a Lok Sabha term in short form (e.g. 17th LS).
export function termShort(n) {
  return `${n}${ordinalSuffix(n)} LS`;
}

// Format a count of items out of a total (e.g. 41 of 1,318 speeches).
export function countOf(n, total, noun) {
  const part = formatNumber(n);
  const whole = formatNumber(total);
  if (noun) {
    return `${part} of ${whole} ${noun}`;
  }
  return `${part} of ${whole}`;
}

// Format a share percentage with count (e.g. 3.1% (41 of 1,318)).
// A total of 0 returns 0 of 0.
// Missing or non-numeric values return an en dash.
export function shareOf(n, total) {
  if (
    n === null ||
    n === undefined ||
    n === "" ||
    total === null ||
    total === undefined ||
    total === ""
  ) {
    return "–";
  }
  const count = Number(n);
  const sum = Number(total);
  if (Number.isNaN(count) || Number.isNaN(sum)) {
    return "–";
  }
  if (sum === 0) {
    return "0 of 0";
  }
  const ratio = (count / sum) * 100;
  const percent = ratio.toFixed(1);
  return `${percent}% (${formatNumber(count)} of ${formatNumber(sum)})`;
}

// Detect Devanagari or Arabic script in text.
// Returns "hi" for Devanagari, "ur" for Arabic script, or undefined.
// The first script letter in the text wins when both are present.
export function scriptLang(text) {
  if (!text || typeof text !== "string") {
    return undefined;
  }
  const match = text.match(/[\u0900-\u097F\u0600-\u06FF]/);
  if (!match) {
    return undefined;
  }
  const code = match[0].charCodeAt(0);
  if (code >= 0x0900 && code <= 0x097F) {
    return "hi";
  }
  if (code >= 0x0600 && code <= 0x06FF) {
    return "ur";
  }
  return undefined;
}
