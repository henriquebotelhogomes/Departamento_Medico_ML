import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { Predict } from "@/pages/Predict";
import "@/i18n";

function createWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Predict (PACS Demo) page", () => {
  it("renders the page title", () => {
    render(<Predict />, { wrapper: createWrapper() });
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("renders the 1-Click Demo sample buttons", () => {
    render(<Predict />, { wrapper: createWrapper() });
    expect(screen.getByText("Normal")).toBeInTheDocument();
    expect(screen.getByText("Covid-19")).toBeInTheDocument();
    expect(screen.getByText("Exame DICOM (.dcm)")).toBeInTheDocument();
  });

  it("shows placeholder text when no result is loaded", () => {
    render(<Predict />, { wrapper: createWrapper() });
    expect(screen.getByRole("heading", { name: /estação de demonstração pacs/i })).toBeInTheDocument();
  });

  it("offers direct link to New Exam page", () => {
    render(<Predict />, { wrapper: createWrapper() });
    expect(screen.getByText(/ir para novo exame/i)).toBeInTheDocument();
  });
});
