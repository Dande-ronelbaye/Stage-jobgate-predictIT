import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import axios from "axios";
import { Sparkles, Loader2 } from "lucide-react";
import { useAuth } from "./AuthContext";

// Vite expose les variables préfixées VITE_ via import.meta.env.
// Si lib/api.ts a déjà une instance axios centralisée avec une baseURL,
// remplace API_BASE_URL ci-dessous par cette instance pour éviter la duplication.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function LoginPage() {
  const navigate = useNavigate();
  const { refetchUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await axios.post(
        `${API_BASE_URL}/api/auth/login`,
        { email, password, remember_me: rememberMe },
        { withCredentials: true } // indispensable : envoie/reçoit le cookie httpOnly
      );
      refetchUser(); // sans ça, NavBar reste sur l'ancien état "déconnecté"
      navigate({ to: "/" });
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        setError("Email ou mot de passe incorrect.");
      } else {
        setError("Une erreur est survenue. Réessaie dans un instant.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen">
      <div className="app-aura" />
      <div className="pointer-events-none fixed inset-0 -z-10 grid-overlay opacity-40" />

      <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-4 py-12">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="gradient-bg relative grid h-12 w-12 place-items-center rounded-xl shadow-lg">
            <Sparkles className="h-6 w-6 text-white" />
            <span className="absolute inset-0 rounded-xl bg-white/10" />
          </div>
          <h1 className="mt-4 font-display text-2xl font-bold tracking-tight">
            Connexion à <span className="gradient-text">PredictIT</span>
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Accède à tes analyses de marché sauvegardées.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="glass space-y-4 rounded-2xl p-6">
          {error && (
            <div className="rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label htmlFor="email" className="text-sm font-medium text-foreground">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
              placeholder="toi@exemple.com"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="password" className="text-sm font-medium text-foreground">
              Mot de passe
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
              placeholder="••••••••"
            />
          </div>

          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 rounded border-border accent-primary"
            />
            Se souvenir de moi
          </label>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {loading ? "Connexion..." : "Se connecter"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Pas encore de compte ?{" "}
          <Link to="/signup" className="font-medium text-foreground hover:underline">
            Créer un compte
          </Link>
        </p>
      </main>
    </div>
  );
}