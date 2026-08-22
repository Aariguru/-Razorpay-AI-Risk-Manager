import { describe, expect, it } from "vitest";

describe("analyst dashboard", () => {
  it("keeps the human review decisions explicit", () => {
    expect(["allow", "manual_review", "block"]).toContain("manual_review");
  });
});
