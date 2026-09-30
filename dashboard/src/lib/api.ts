import axios from "axios";

export const API_BASE_URL = "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// --- type de marché réutilisable ---
export type Market = "tunisia" | "france" | "remote";

export interface PredictPayload {
  city: string;
  experience?: "junior" | "intermediate" | "senior"; // optionnel
  contract: "cdi" | "freelance" | "cdd" | "alternance";
  technologies: string[];
  market: Market;
}

export interface CitySalary {
  city: string;
  salary: number;
}

export interface TechShare {
  tech: string;
  demand: number;
}

export interface PredictResponse {
  salary: number;
  currency: "EUR";
  period: "year";
  marketMin: number;
  marketMax: number;
  marketMedian: number;
  percentile: number; // 0..100
  cities: CitySalary[];
  techDemand: TechShare[];
}

// --- TYPES POUR LE MARKET DASHBOARD ---
export interface KPIStats {
  total_offers: number;
  sources_count: number;
  duplicates_removed_pct: number;
  model_accuracy_pct: number;
}

export interface SkillCount {
  name: string;
  count: number;
}

export interface AnalyticsStatsResponse {
  kpis: KPIStats;
  skills: SkillCount[];
}

// --- TYPES POUR LE GAP ANALYSIS ---
export interface GapRecommendation {
  skill: string;
  unlocked_offers_count: number;
  new_coverage_pct: number;
}

export interface GapAnalysisResponse {
  user_techs: string[];
  total_offers: number;
  current_qualifying_count: number;
  current_qualifying_pct: number;
  recommendations: GapRecommendation[];
}

// Paramètres du gap analysis -- technologies est le seul champ obligatoire,
// le reste (market/city/contract/experience) est optionnel et sert de
// filtre best-effort côté backend (voir endpoints_market_intelligence.py).
export interface GapAnalysisParams {
  technologies: string[];
  market?: Market;
  city?: string;
  contract?: PredictPayload["contract"];
  experience?: PredictPayload["experience"];
}

/**
 * Appel à l'API FastAPI pour la prédiction de salaire.
 * Endpoint : POST /api/predict
 *
 * NOTE : n'est plus appelé par PredictionForm -- le bouton "Générer mon
 * rapport de marché" appelle désormais fetchGapAnalysis(). Cette fonction
 * reste disponible si tu veux une prédiction de salaire ailleurs dans
 * l'app, mais n'est plus câblée au formulaire de profil.
 */
export async function predictSalary(payload: PredictPayload): Promise<PredictResponse> {
  const { data } = await api.post("/api/predict", payload);

  return {
    ...data,
    currency: "EUR",
    period: "year",
  };
}

/**
 * Récupération des statistiques globales et compétences par marché
 * Endpoint : GET /api/analytics/stats?market=tunisia|france
 */
export async function fetchAnalyticsStats(market: Exclude<Market, "remote">): Promise<AnalyticsStatsResponse> {
  const { data } = await api.get<AnalyticsStatsResponse>("/api/analytics/stats", {
    params: { market },
  });
  return data;
}

/**
 * Récupération des recommandations de compétences et taux de qualification (Gap Analysis)
 * Endpoint : GET /api/analytics/gap-analysis?techs=...&market=...&city=...&contract=...&experience=...
 *
 * Seul `technologies` est obligatoire. Les autres champs sont des filtres
 * best-effort (détection par regex côté backend, pas de champ structuré
 * fiable dans les données scrapées pour city/contract/experience).
 */
export async function fetchGapAnalysis(params: GapAnalysisParams): Promise<GapAnalysisResponse> {
  const { data } = await api.get<GapAnalysisResponse>("/api/analytics/gap-analysis", {
    params: {
      techs: params.technologies.join(","),
      market: params.market,
      city: params.city,
      contract: params.contract,
      experience: params.experience,
    },
  });
  return data;
}