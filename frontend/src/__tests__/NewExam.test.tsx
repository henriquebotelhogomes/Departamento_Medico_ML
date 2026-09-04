import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { NewExam } from "@/pages/NewExam";
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

describe("NewExam page", () => {
  it("renders the page title", () => {
    render(<NewExam />, { wrapper: createWrapper() });
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Novo Exame Radiológico");
  });

  it("renders the upload drop zone and select button", () => {
    render(<NewExam />, { wrapper: createWrapper() });
    expect(screen.getByText(/arraste e solte o exame aqui/i)).toBeInTheDocument();
    expect(screen.getByText(/selecionar arquivo do computador/i)).toBeInTheDocument();
  });

  it("shows error for unsupported file type", async () => {
    const { container } = render(<NewExam />, { wrapper: createWrapper() });

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["test"], "test.txt", { type: "text/plain" });

    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText(/formato não suportado/i)).toBeInTheDocument();
  });

  it("shows file ready state and analysis button when valid file is selected", async () => {
    const { container } = render(<NewExam />, { wrapper: createWrapper() });

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["dummy data"], "patient_chest.png", { type: "image/png" });

    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText("patient_chest.png")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /analisar exame & gerar laudo/i })).toBeInTheDocument();
  });
});
