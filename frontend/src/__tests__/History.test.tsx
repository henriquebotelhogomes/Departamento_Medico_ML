import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { History } from "@/pages/History";
import "@/i18n";

// Mock the API module
vi.mock("@/lib/api", () => ({
  fetchHistory: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  deletePrediction: vi.fn(),
}));

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

describe("History page", () => {
  it("renders the page title", () => {
    render(<History />, { wrapper: createWrapper() });
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("renders the class filter dropdown", () => {
    render(<History />, { wrapper: createWrapper() });
    const select = screen.getByRole("combobox");
    expect(select).toBeInTheDocument();
  });

  it("renders table headers", async () => {
    render(<History />, { wrapper: createWrapper() });
    // Wait for loading to finish
    const table = await screen.findByRole("table");
    expect(table).toBeInTheDocument();
  });

  it("shows empty state when no predictions", async () => {
    render(<History />, { wrapper: createWrapper() });
    // In pt-BR: "Nenhuma predição" or en: "No predictions"
    const emptyText = await screen.findByText(/nenhuma|no predictions/i);
    expect(emptyText).toBeInTheDocument();
  });
});
