import { fireEvent, render, screen } from "@testing-library/react";
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

describe("Predict page", () => {
  it("renders the page title", () => {
    render(<Predict />, { wrapper: createWrapper() });
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("renders the upload drop zone", () => {
    render(<Predict />, { wrapper: createWrapper() });
    // In pt-BR: "Arraste e solte" or en: "Drag & drop"
    const dropText = screen.getByText(/arraste|drag/i);
    expect(dropText).toBeInTheDocument();
  });

  it("run prediction button is disabled without file", () => {
    render(<Predict />, { wrapper: createWrapper() });
    const btn = screen.getByRole("button", { name: /execut|run/i });
    expect(btn).toBeDisabled();
  });

  it("shows error for unsupported file type", async () => {
    const { container } = render(<Predict />, { wrapper: createWrapper() });

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["test"], "test.txt", { type: "text/plain" });

    fireEvent.change(input, { target: { files: [file] } });

    // In pt-BR: "Tipo de arquivo não suportado" or en: "Unsupported file type"
    expect(screen.getByText(/tipo de arquivo|unsupported/i)).toBeInTheDocument();
  });

  it("shows placeholder text when no result", () => {
    render(<Predict />, { wrapper: createWrapper() });
    // In pt-BR: "resultados da predição" or en: "Prediction results"
    expect(screen.getByText(/resultados|prediction results/i)).toBeInTheDocument();
  });
});
