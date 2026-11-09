import { describe, expect, it } from "vitest";
import { tidyTitle } from "../assets/js/titles.js";

describe("tidyTitle", () => {
  it("turns ?Contd.. into (contd.) and keeps the rest of the title", () => {
    expect(
      tidyTitle("The Constitution (One Hundred and Thirty-First Amendment) Bill, 2026 and Delimitation Bill, 2026?Contd.. - not passed")
    ).toBe("The Constitution (One Hundred and Thirty-First Amendment) Bill, 2026 and Delimitation Bill, 2026 (contd.) - not passed");
    expect(tidyTitle("Demands for Grants Contd..")).toBe("Demands for Grants (contd.)");
  });

  it("strips a trailing -laid or - laid", () => {
    expect(tidyTitle("Need to ensure daily payment of wages to the job card holders under MGNREGA-laid")).toBe(
      "Need to ensure daily payment of wages to the job card holders under MGNREGA"
    );
    expect(tidyTitle("Re: Augmentation of the Scheme- laid")).toBe("Re: Augmentation of the Scheme");
  });

  it("collapses doubled dots and spaces, and handles empty input", () => {
    expect(tidyTitle("Budget..  General   Discussion")).toBe("Budget. General Discussion");
    expect(tidyTitle(null)).toBe("");
    expect(tidyTitle("  Plain title ")).toBe("Plain title");
  });
});
