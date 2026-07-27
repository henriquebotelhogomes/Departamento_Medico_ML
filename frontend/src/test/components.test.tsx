import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProbabilityBar } from "@/components/ProbabilityBar";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import "@/i18n";

describe("ProbabilityBar", () => {
  it("renders label and percentage", () => {
    render(<ProbabilityBar classId={0} label="Covid-19" probability={0.923} />);
    expect(screen.getByText("Covid-19")).toBeInTheDocument();
    expect(screen.getByText("92.3%")).toBeInTheDocument();
  });

  it("exposes an accessible progressbar with the right value", () => {
    render(<ProbabilityBar classId={1} label="Normal" probability={0.5} />);
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "50");
  });
});

describe("ConfidenceBadge", () => {
  it("formats confidence as a percentage", () => {
    render(<ConfidenceBadge confidence={0.876} />);
    // i18n: "87.6% confidence" or "87.6% de confiança"
    expect(screen.getByText(/87\.6%/)).toBeInTheDocument();
  });
});
