// Clean the oddities of a debate title that the source data holds.
// "?Contd.." and "Contd.." become " (contd.)". A trailing "-laid" goes away. Doubled dots and spaces collapse.
export function tidyTitle(title) {
  if (title === null || title === undefined) return "";
  return String(title)
    .replace(/\s*\??\s*Contd\.*/gi, " (contd.)")
    .replace(/\s*-\s*laid\s*$/i, "")
    .replace(/\.{2,}/g, ".")
    .replace(/\s{2,}/g, " ")
    .trim();
}
