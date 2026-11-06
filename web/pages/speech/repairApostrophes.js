// The source text lost some quote marks. They show as "?" in the data.
// Torko repairs one case only: a letter, then "?s", then the end of the word. That case is an apostrophe and cannot be a question.
// The repair keeps the length of the text, so the offsets of the marks stay valid.
export function repairApostrophes(text) {
  if (!text) return "";
  return String(text).replace(/(\p{L})\?s(?![\p{L}\p{N}])/gu, "$1’s");
}
