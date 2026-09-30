import { useState } from "react";
import { ChevronDown, ExternalLink, Copy, Check } from "lucide-react";

/**
 * Contenu basé sur les routes réellement présentes dans main.py.
 * Si une route change (params, nom, réponse), mets à jour l'entrée
 * correspondante ici — cette page ne lit pas le code du backend,
 * elle le décrit à la main (contrairement à /docs qui est auto-générée).
 */

type Method = "GET" | "POST";

interface Param {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

interface Endpoint {
  method: Method;
  path: string;
  category: string;
  summary: string;
  description: string;
  params?: Param[];
  exampleResponse: string;
}

const ENDPOINTS: Endpoint[] = [
  {
    method: "POST",
    path: "/api/predict",
    category: "Prédiction",
    summary: "Prédit un salaire à partir du profil fourni",
    description:
      "Utilise le modèle Random Forest entraîné pour estimer un salaire, puis le compare aux offres réelles en base (médiane, min/max marché, percentile). Ignoré pour market=\"tunisia\" côté frontend (modèle non entraîné sur des données tunisiennes).",
    params: [
      { name: "city", type: "string", required: true, description: "Ville ciblée" },
      { name: "contract", type: "string", required: true, description: "Type de contrat" },
      { name: "technologies", type: "string[]", required: true, description: "Liste de technos" },
      { name: "market", type: "string", required: true, description: "\"tunisia\" | \"france\" | autre" },
      { name: "experience", type: "string", required: false, description: "junior | intermediate | senior" },
    ],
    exampleResponse: `{
  "salary": 2400,
  "marketMedian": 2300,
  "marketMin": 1800,
  "marketMax": 3200,
  "percentile": 62,
  "cities": [{ "city": "Tunis", "salary": 2100 }, ...],
  "techDemand": [{ "tech": "React", "demand": 80 }, ...]
}`,
  },
  {
    method: "GET",
    path: "/api/analytics/stats",
    category: "Analytics",
    summary: "KPIs globaux + top 8 technos demandées",
    description:
      "Compte les offres par marché et extrait les technologies les plus fréquentes depuis techs_principales, avec normalisation des noms (ex: 'js' → 'JavaScript').",
    params: [
      { name: "market", type: "string", required: false, description: "\"tunisia\" (défaut) | \"france\"" },
    ],
    exampleResponse: `{
  "kpis": {
    "total_offers": 2648,
    "sources_count": 3,
    "duplicates_removed_pct": 89,
    "model_accuracy_pct": 84.2
  },
  "skills": [{ "name": "Python", "count": 312 }, ...]
}`,
  },
  {
    method: "GET",
    path: "/api/analytics/gap-analysis",
    category: "Analytics",
    summary: "Compétences manquantes les plus rentables à apprendre",
    description:
      "Compare les technos de l'utilisateur aux offres en base : calcule le % d'offres déjà qualifiantes, puis classe les compétences manquantes par nombre d'offres débloquées si apprises.",
    params: [
      { name: "techs", type: "string", required: false, description: "Technos séparées par virgules, ex: \"python,react\"" },
    ],
    exampleResponse: `{
  "user_techs": ["Python", "React"],
  "total_offers": 2648,
  "current_qualifying_count": 340,
  "current_qualifying_pct": 12.8,
  "recommendations": [
    { "skill": "Docker", "unlocked_offers_count": 210, "new_coverage_pct": 20.7 },
    ...
  ]
}`,
  },
  {
    method: "GET",
    path: "/api/analytics/trends",
    category: "Analytics",
    summary: "Évolution des technos par période",
    description:
      "Découpe les offres (triées par id croissant, faute de champ date) en n_periods tranches égales et compte les occurrences de chaque techno par tranche. \"Période\" ≠ mois calendaire — c'est un proxy chronologique basé sur l'ordre d'insertion.",
    params: [
      { name: "market", type: "string", required: false, description: "\"tunisia\" (défaut) | \"france\"" },
      { name: "n_periods", type: "int", required: false, description: "Nombre de tranches (défaut 12)" },
      { name: "top_n", type: "int", required: false, description: "Nombre de technos retournées (défaut 10)" },
    ],
    exampleResponse: `{
  "periods_total": 12,
  "skills": [
    {
      "skill": "React",
      "points": [{ "period": "Période 1", "count": 8 }, ...]
    },
    ...
  ]
}`,
  },
  {
    method: "GET",
    path: "/api/analytics/pairs",
    category: "Analytics",
    summary: "Compétences associées (co-occurrence + lift)",
    description:
      "Calcule pour chaque paire de technos apparaissant ensemble sur une offre le lift = support(A,B) / (support(A) × support(B)). Un lift élevé signifie que les deux technos apparaissent ensemble bien plus souvent que si c'était le hasard.",
    params: [
      { name: "market", type: "string", required: false, description: "\"tunisia\" (défaut) | \"france\"" },
      { name: "min_cooccurrence", type: "int", required: false, description: "Seuil minimum de co-apparitions (défaut 3)" },
      { name: "top_n", type: "int", required: false, description: "Nombre de paires retournées (défaut 50)" },
    ],
    exampleResponse: `{
  "total_offers": 2648,
  "pairs": [
    { "skillA": "Docker", "skillB": "Kubernetes", "coOccurrence": 45, "lift": 3.2 },
    ...
  ]
}`,
  },
  {
    method: "GET",
    path: "/api/jobs",
    category: "Données brutes",
    summary: "Liste paginée des offres, avec filtres optionnels",
    description: "Accès direct aux offres stockées, filtrable par ville et technologie.",
    params: [
      { name: "limit", type: "int", required: false, description: "Nombre max de résultats (défaut 50)" },
      { name: "ville", type: "string", required: false, description: "Filtre par ville (recherche partielle)" },
      { name: "tech", type: "string", required: false, description: "Filtre par techno (recherche partielle)" },
    ],
    exampleResponse: `{
  "total": 50,
  "jobs": [{ "id": 1, "title": "...", "ville": "Tunis", ... }, ...]
}`,
  },
  {
    method: "GET",
    path: "/",
    category: "Système",
    summary: "Health check",
    description: "Vérifie que l'API et la connexion PostgreSQL sont opérationnelles.",
    exampleResponse: `{
  "message": "Bienvenue sur l'API de PredictIT ! PostgreSQL et le modèle IA sont opérationnels."
}`,
  },
];

const CATEGORIES = Array.from(new Set(ENDPOINTS.map((e) => e.category)));

const METHOD_STYLES: Record<Method, string> = {
  GET: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
  POST: "bg-sky-500/15 text-sky-300 border-sky-400/30",
};

// Ajuste si ton instance axios centralisée a déjà une baseURL configurée.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function ApiPage() {
  const [openPath, setOpenPath] = useState<string | null>(ENDPOINTS[0].path);
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  const copyUrl = async (path: string) => {
    try {
      await navigator.clipboard.writeText(`${API_BASE_URL}${path}`);
      setCopiedPath(path);
      setTimeout(() => setCopiedPath(null), 1500);
    } catch {
      // silencieux — pas critique si le clipboard échoue
    }
  };

  const docsUrl = API_BASE_URL + "/docs";

  return (
    <div className="min-h-screen bg-background text-foreground p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Documentation API</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {ENDPOINTS.length} endpoints exposés par le backend FastAPI de PredictIT.
          </p>
        </div>
        <a
          href={docsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 glass rounded-xl px-4 py-2 text-sm text-foreground hover:text-foreground hover:border-border transition-colors">
          Tester en direct (Swagger)
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>

      {/* Sections par catégorie */}
      {CATEGORIES.map((category) => (
        <div key={category} className="space-y-3">
          <h2 className="text-xs uppercase tracking-wide text-muted-foreground px-1">{category}</h2>
          {ENDPOINTS.filter((e) => e.category === category).map((endpoint) => {
            const isOpen = openPath === endpoint.path;
            const methodBadgeClass =
              "text-xs font-mono font-semibold px-2 py-1 rounded-md border " + METHOD_STYLES[endpoint.method];
            const chevronClass =
              "h-4 w-4 text-muted-foreground ml-auto transition-transform" + (isOpen ? " rotate-180" : "");
            return (
              <div key={endpoint.path} className="glass rounded-2xl overflow-hidden">
                <button
                  onClick={() => setOpenPath(isOpen ? null : endpoint.path)}
                  className="w-full flex items-center gap-3 px-5 py-4 text-left">
                  <span className={methodBadgeClass}>
                    {endpoint.method}
                  </span>
                  <code className="text-sm text-foreground font-mono">{endpoint.path}</code>
                  <span className="text-sm text-muted-foreground hidden sm:inline">— {endpoint.summary}</span>
                  <ChevronDown className={chevronClass} />
                </button>

                {isOpen && (
                  <div className="px-5 pb-5 space-y-4 border-t border-border/50 pt-4">
                    <p className="text-sm text-muted-foreground leading-relaxed">{endpoint.description}</p>

                    <div className="flex items-center gap-2">
                      <code className="flex-1 text-xs text-muted-foreground bg-muted rounded-lg px-3 py-2 font-mono overflow-x-auto">
                        {API_BASE_URL}
                        {endpoint.path}
                      </code>
                      <button
                        onClick={() => copyUrl(endpoint.path)}
                        className="shrink-0 flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground border border-border rounded-lg px-3 py-2 transition-colors">
                        {copiedPath === endpoint.path ? (
                          <>
                            <Check className="h-3.5 w-3.5" /> Copié
                          </>
                        ) : (
                          <>
                            <Copy className="h-3.5 w-3.5" /> Copier
                          </>
                        )}
                      </button>
                    </div>

                    {endpoint.params && endpoint.params.length > 0 && (
                      <div>
                        <div className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
                          Paramètres
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="text-left text-muted-foreground border-b border-border">
                                <th className="py-1.5 pr-4 font-normal">Nom</th>
                                <th className="py-1.5 pr-4 font-normal">Type</th>
                                <th className="py-1.5 pr-4 font-normal">Requis</th>
                                <th className="py-1.5 pr-4 font-normal">Description</th>
                              </tr>
                            </thead>
                            <tbody>
                              {endpoint.params.map((p) => (
                                <tr key={p.name} className="border-b border-border/50">
                                  <td className="py-1.5 pr-4 font-mono text-foreground">{p.name}</td>
                                  <td className="py-1.5 pr-4 text-muted-foreground font-mono">{p.type}</td>
                                  <td className="py-1.5 pr-4 text-muted-foreground">
                                    {p.required ? "Oui" : "Non"}
                                  </td>
                                  <td className="py-1.5 pr-4 text-muted-foreground">{p.description}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    <div>
                      <div className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
                        Exemple de réponse
                      </div>
                      <pre className="text-xs text-foreground bg-muted rounded-lg p-3 overflow-x-auto font-mono leading-relaxed">
                        {endpoint.exampleResponse}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}