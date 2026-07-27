import { describe, expect, it, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { Login } from "@/pages/Login";
import "@/i18n";

function renderLogin() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("Login page", () => {
  beforeEach(() => localStorage.clear());

  it("shows the demo credentials hint", async () => {
    renderLogin();
    // i18n: heading is "Sign in" or "Entrar"
    await waitFor(() =>
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument(),
    );
    expect(screen.getByText(/demo123 \/ demo123/)).toBeInTheDocument();
  });

  it("fills demo credentials when the helper button is clicked", async () => {
    const user = userEvent.setup();
    renderLogin();
    await waitFor(() =>
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument(),
    );
    // Button text varies by language: "Fill demo credentials" or "Preencher credenciais demo"
    const fillBtn = screen.getByRole("button", { name: /fill|preencher/i });
    await user.click(fillBtn);
    // Input labels vary: "Username or email" or "Usuário ou e-mail"
    const usernameInput = screen.getByLabelText(/username|usu\u00e1rio/i);
    const passwordInput = screen.getByLabelText(/password|senha/i);
    expect(usernameInput).toHaveValue("demo123");
    expect(passwordInput).toHaveValue("demo123");
  });
});
