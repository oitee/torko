import { describe, expect, it } from "vitest";
import { repairApostrophes } from "../pages/speech/repairApostrophes.js";

describe("repairApostrophes", () => {
  it("repairs only a letter, then ?s, then the end of the word", () => {
    expect(repairApostrophes("India?s farmers")).toBe("India’s farmers");
    expect(repairApostrophes("the people?s right.")).toBe("the people’s right.");
  });
  it("keeps a real question and a lost quote mark as they are", () => {
    expect(repairApostrophes("Is it so? said the member")).toBe("Is it so? said the member");
    expect(repairApostrophes("said,?The right to life")).toBe("said,?The right to life");
    expect(repairApostrophes("?sir")).toBe("?sir");
  });
});
