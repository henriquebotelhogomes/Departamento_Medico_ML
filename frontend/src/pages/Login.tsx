import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ScanLine } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/context/AuthContext";
import { apiError } from "@/lib/api";

export function Login() {
  const { user, login } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/predict";

  if (user) return <Navigate to={from} replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(apiError(err, t("auth.login_failed")));
    } finally {
      setSubmitting(false);
    }
  }

  function fillDemo() {
    setUsername("demo123");
    setPassword("demo123");
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <span className="mb-2 inline-flex items-center gap-2 text-2xl font-bold text-brand-600 dark:text-brand-400">
            <ScanLine className="h-6 w-6" /> {t("brand")}
          </span>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {t("brand_tagline")}
          </p>
        </div>

        <form onSubmit={onSubmit} className="card space-y-4">
          <h1 className="text-lg font-semibold">{t("auth.sign_in")}</h1>
          {error && (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          )}
          <div>
            <label className="label" htmlFor="username">
              {t("auth.username_or_email")}
            </label>
            <input
              id="username"
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className="label" htmlFor="password">
              {t("auth.password")}
            </label>
            <input
              id="password"
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <button type="submit" className="btn-primary w-full" disabled={submitting}>
            {submitting ? t("auth.signing_in") : t("auth.sign_in")}
          </button>
        </form>

        <div className="mt-4 rounded-lg border border-slate-300 bg-slate-100 p-3 text-center text-sm dark:border-slate-600 dark:bg-slate-800">
          <p className="text-slate-900 dark:text-white">
            {t("auth.demo_hint")} <code className="rounded bg-slate-200 px-1.5 py-0.5 font-bold text-slate-900 dark:bg-slate-700 dark:text-white">{t("auth.demo_credentials")}</code>
          </p>
          <button onClick={fillDemo} className="mt-2 font-semibold text-brand-600 hover:underline dark:text-brand-300">
            {t("auth.fill_demo")}
          </button>
        </div>

        <p className="mt-4 text-center text-sm text-slate-500 dark:text-slate-400">
          {t("auth.no_account")}{" "}
          <Link to="/register" className="font-medium text-brand-600 hover:underline dark:text-brand-400">
            {t("auth.create_one")}
          </Link>
        </p>
      </div>
    </div>
  );
}
