import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ScanLine } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/context/AuthContext";
import { apiError, register as apiRegister } from "@/lib/api";

export function Register() {
  const { user, login } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/predict" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiRegister(username, email, password);
      await login(username, password);
      navigate("/predict", { replace: true });
    } catch (err) {
      setError(apiError(err, t("auth.registration_failed")));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <span className="mb-2 inline-flex items-center gap-2 text-2xl font-bold text-brand-600 dark:text-brand-400">
            <ScanLine className="h-6 w-6" /> {t("brand")}
          </span>
        </div>
        <form onSubmit={onSubmit} className="card space-y-4">
          <h1 className="text-lg font-semibold">{t("auth.create_account")}</h1>
          {error && (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          )}
          <div>
            <label className="label" htmlFor="username">{t("auth.username")}</label>
            <input
              id="username"
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              minLength={3}
              required
            />
          </div>
          <div>
            <label className="label" htmlFor="email">{t("auth.email")}</label>
            <input
              id="email"
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label" htmlFor="password">{t("auth.password")}</label>
            <input
              id="password"
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={6}
              required
            />
          </div>
          <button type="submit" className="btn-primary w-full" disabled={submitting}>
            {submitting ? t("auth.creating") : t("auth.create_account")}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500 dark:text-slate-400">
          {t("auth.already_have_account")}{" "}
          <Link to="/login" className="font-medium text-brand-600 hover:underline dark:text-brand-400">
            {t("auth.sign_in")}
          </Link>
        </p>
      </div>
    </div>
  );
}
