import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Activity, Globe, LayoutDashboard, LogOut, Moon, ScanLine, Sun } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";

const navItems = [
  { to: "/predict", key: "nav.predict", icon: ScanLine },
  { to: "/history", key: "nav.history", icon: Activity },
  { to: "/dashboard", key: "nav.dashboard", icon: LayoutDashboard },
];

export function Layout() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();

  const toggleLang = () => {
    const next = i18n.language === "pt-BR" ? "en" : "pt-BR";
    void i18n.changeLanguage(next);
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-2 text-lg font-bold text-brand-600 dark:text-brand-400">
              <ScanLine className="h-5 w-5" /> {t("brand")}
            </span>
            <nav className="hidden gap-1 sm:flex">
              {navItems.map(({ to, key, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                        : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                    }`
                  }
                >
                  <Icon className="h-4 w-4" /> {t(key)}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleLang}
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label={t("language.label")}
              title={t("language.label")}
            >
              <Globe className="h-4 w-4" />
            </button>
            <button
              onClick={toggle}
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label={t("common.toggle_theme")}
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <span className="hidden text-sm text-slate-500 dark:text-slate-400 sm:inline">
              {user?.username}
            </span>
            <button onClick={handleLogout} className="btn-secondary" aria-label={t("auth.logout")}>
              <LogOut className="h-4 w-4" /> {t("auth.logout")}
            </button>
          </div>
        </div>
        <nav className="flex gap-1 border-t border-slate-100 px-4 py-2 dark:border-slate-800 sm:hidden">
          {navItems.map(({ to, key, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium ${
                  isActive
                    ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                    : "text-slate-600 dark:text-slate-300"
                }`
              }
            >
              <Icon className="h-4 w-4" /> {t(key)}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
