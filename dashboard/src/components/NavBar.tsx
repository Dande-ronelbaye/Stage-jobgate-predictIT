import { Sparkles, LogOut, User } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { Link, useNavigate } from "@tanstack/react-router";
import { useAuth } from "./AuthContext";


export function NavBar() {
  const { user, isLoading, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate({ to: "/" });
  };

  return (
    <header className="sticky top-4 z-40 mx-auto w-full max-w-7xl px-4">
      <nav className="glass flex items-center justify-between rounded-2xl px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="gradient-bg relative grid h-9 w-9 place-items-center rounded-xl shadow-lg">
            <Sparkles className="h-4 w-4 text-white" />
            <span className="absolute inset-0 rounded-xl bg-white/10" />
          </div>
          <div className="flex flex-col leading-none">
            <span className="font-display text-lg font-bold tracking-tight">
              Predict<span className="gradient-text">IT</span>
            </span>
            <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
              TECH MARKET & CAREER INTELLIGENCE
            </span>
          </div>
        </div>

        <div className="hidden items-center gap-6 md:flex">
          <Link className="text-sm text-muted-foreground transition-colors hover:text-foreground" to="/">Dashboard</Link>
          <Link className="text-sm text-muted-foreground transition-colors hover:text-foreground" to="/trends">Trends</Link>
          <Link className="text-sm text-muted-foreground transition-colors hover:text-foreground" to="/api">API</Link>
        </div>

        <div className="flex items-center gap-3">
          {!isLoading && (
            isAuthenticated ? (
              <div className="hidden items-center gap-2 sm:flex">
                <span className="glass flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs text-muted-foreground">
                  <User className="h-3.5 w-3.5" />
                  {user?.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="glass flex h-9 items-center gap-1.5 rounded-full px-3 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground">
                  <LogOut className="h-3.5 w-3.5" />
                  Déconnexion
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="glass hidden h-9 items-center rounded-full px-4 text-sm font-medium transition-transform hover:scale-[1.03] sm:inline-flex">
                Connexion
              </Link>
            )
          )}
          <ThemeToggle />
        </div>
      </nav>
    </header>
  );
}