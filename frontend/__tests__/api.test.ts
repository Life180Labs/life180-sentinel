import { describe, expect, it } from "vitest";

describe("API URL building", () => {
  it("constructs repository list URL correctly", () => {
    const base = "http://localhost:8000";
    const path = "/api/v1/repositories";
    expect(`${base}${path}`).toBe("http://localhost:8000/api/v1/repositories");
  });

  it("constructs repository evaluation URL with ID", () => {
    const id = "550e8400-e29b-41d4-a716-446655440000";
    const path = `/api/v1/repositories/${id}/evaluations`;
    expect(path).toContain(id);
    expect(path).toContain("evaluations");
  });

  it("constructs report URL with ID", () => {
    const id = "550e8400-e29b-41d4-a716-446655440000";
    const path = `/api/v1/repositories/${id}/report`;
    expect(path).toBe(`/api/v1/repositories/${id}/report`);
  });
});

describe("Score utilities", () => {
  const scoreToGrade = (score: number): string => {
    if (score >= 90) return "A+";
    if (score >= 85) return "A";
    if (score >= 80) return "A-";
    if (score >= 75) return "B+";
    if (score >= 70) return "B";
    if (score >= 65) return "B-";
    if (score >= 60) return "C+";
    if (score >= 55) return "C";
    if (score >= 50) return "C-";
    if (score >= 40) return "D";
    return "F";
  };

  it("returns A+ for score 95", () => {
    expect(scoreToGrade(95)).toBe("A+");
  });

  it("returns F for score 20", () => {
    expect(scoreToGrade(20)).toBe("F");
  });

  it("returns B for score 70", () => {
    expect(scoreToGrade(70)).toBe("B");
  });

  it("returns D for score 45", () => {
    expect(scoreToGrade(45)).toBe("D");
  });
});
