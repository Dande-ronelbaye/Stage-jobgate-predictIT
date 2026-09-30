import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useNavigate, Link } from "@tanstack/react-router";
import axios from "axios";
import { Lock } from "lucide-react";
import { PredictionForm } from "@/components/PredictionForm";
import { ResultsPanel } from "@/components/ResultsPanel";
import { MarketDashboard } from "@/components/MarketDashboard";
import { useAuth } from "@/components/AuthContext";
import {
  predictSalary,
  fetchGapAnalysis,
  type PredictPayload,
  type PredictResponse,
  type GapAnalysisResponse,
} from "@/lib/api";

// ⚠️ Si lib/api.ts n'utilise pas déjà une instance axios avec
// withCredentials: true (ou axios.defaults.withCredentials = true réglé
// globalement), predictSalary/fetchGapAnalysis n'enverront pas le cookie
// d'auth et échoueront en 401 même pour un utilisateur connecté.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "PredictIT — TECH MARKET & CAREER INTELLIGENCE" },
      {
        name: "description",
        content:
          "Analysez les tendances tech, évaluez votre valeur salariale et identifiez vos compétences manquantes grâce aux données réelles de milliers d'offres d'emploi.",
      },
      { property: "og:title", content: "PredictIT — TECH MARKET & CAREER INTELLIGENCE" },
      { property: "og:description", content: "Prédiction de salaires tech basée sur l'IA." },
    ],
  }),
  component: Index,
});

async function saveHistory(payload: PredictPayload, predictData: PredictResponse | null, gapData: GapAnalysisResponse) {
  try {
    await axios.post(
      `${API_BASE_URL}/api/history`,
      {
        input_payload: payload,
        predict_result: predictData,
        gap_result: gapData,
      },
      { withCredentials: true }
    );
  } catch (err) {
    // Non-bloquant : si la sauvegarde échoue, l'utilisateur voit quand
    // même ses résultats — on log juste pour debug.
    console.warn("Impossible de sauvegarder l'historique :", err);
  }
}

function Index() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const analysisMutation = useMutation({
    mutationFn: async (payload: PredictPayload) => {
      const gapPromise = fetchGapAnalysis({
        technologies: payload.technologies,
        market: payload.market,
        city: payload.city,
        contract: payload.contract,
        experience: payload.experience,
      });

      // predictSalary est traité comme NON-BLOQUANT et OPTIONNEL :
      // - jamais appelé pour la Tunisie (modèle jamais entraîné dessus)
      // - pour tout le reste (France, Remote...), on l'essaie mais on ne
      //   fait pas planter tout le rapport s'il échoue (ex: le backend
      //   /api/predict pourrait ne pas accepter market="remote" -- sans
      //   ce garde-fou, ça faisait échouer aussi le gap analysis, qui
      //   lui n'a aucune raison de dépendre du salaire).
      let predictData: PredictResponse | null = null;
      if (payload.market !== "tunisia") {
        try {
          predictData = await predictSalary(payload);
        } catch (err) {
          console.warn("predictSalary a échoué, on continue sans le bloc salaire :", err);
          predictData = null;
        }
      }

      const gapData = await gapPromise;

      // Sauvegarde en historique — silencieuse, ne bloque pas l'affichage
      // des résultats si elle échoue.
      await saveHistory(payload, predictData, gapData);

      return { predictData, gapData };
    },
    onSuccess: (data) => {
      console.log("Analyse combinée reçue avec succès !", data);
    },
    onError: (err) => {
      console.error("Erreur lors de la communication avec FastAPI :", err);
    },
  });

  const handleSubmit = (payload: PredictPayload) => {
    if (!isAuthenticated) {
      navigate({ to: "/login" });
      return;
    }
    analysisMutation.mutate(payload);
  };

  return (
    <div className="relative min-h-screen">
      <div className="app-aura" />
      <div className="pointer-events-none fixed inset-0 -z-10 grid-overlay opacity-40" />

      <main className="mx-auto w-full max-w-7xl px-4 py-8 md:py-12 space-y-16">
        {/* Hero */}
        <section className="mx-auto max-w-3xl text-center">
          <span className="glass inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-primary" />
            </span>
            <span className="text-muted-foreground">⚡ Prédictions, Tendances & Recommandations Stack</span>
          </span>
          <h1 className="mt-5 font-display text-4xl font-black leading-[1.05] tracking-tight md:text-6xl">
            Pilote ta <span className="gradient-text">carrière IT</span> grâce à la Data du marché.
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-sm text-muted-foreground md:text-base">
            Analysez les tendances tech, évaluez votre valeur salariale et identifiez vos compétences manquantes grâce aux données réelles de milliers d'offres d'emploi.
          </p>
        </section>

        {/* Split layout (Formulaire + Résultats) — uniquement si connecté */}
        {authLoading ? null : isAuthenticated ? (
          <section className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <PredictionForm
              onSubmit={handleSubmit}
              loading={analysisMutation.isPending}
            />

            <ResultsPanel
              status={
                analysisMutation.isPending
                  ? "loading"
                  : analysisMutation.isSuccess
                  ? "success"
                  : "idle"
              }
              data={analysisMutation.data?.predictData || null}
              gapData={analysisMutation.data?.gapData || null}
            />
          </section>
        ) : (
          <section className="glass mx-auto flex max-w-2xl flex-col items-center gap-4 rounded-2xl px-6 py-10 text-center">
            <div className="gradient-bg grid h-12 w-12 place-items-center rounded-xl shadow-lg">
              <Lock className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">Connecte-toi pour lancer une analyse</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Ton profil, ton positionnement salarial et tes recommandations de compétences seront sauvegardés dans ton historique.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Link
                to="/login"
                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90">
                Se connecter
              </Link>
              <Link
                to="/signup"
                className="glass rounded-lg px-4 py-2 text-sm font-medium text-foreground transition-opacity hover:opacity-90">
                Créer un compte
              </Link>
            </div>
          </section>
        )}

        {/* 📊 Section Market Dashboard Analytics */}
        <section className="w-full pt-4">
          <MarketDashboard />
        </section>

        {/* Footer */}
        <footer className="pt-8 text-center text-xs text-muted-foreground">
          Built with FastAPI · React 19 · TanStack Start —
          <span className="ml-1 gradient-text font-semibold">PredictIT © 2026</span>
        </footer>
      </main>
    </div>
  );
}