import { Briefcase, MapPin, Sparkles, Zap } from "lucide-react";
import { useState } from "react";
import type { PredictPayload } from "@/lib/api";
import { TagInput } from "./TagInput";

const CITIES = ["Paris", "Lyon", "Bordeaux", "Toulouse", "Nantes", "Remote", "Sousse", "Tunis"];

const EXPERIENCE: { key: NonNullable<PredictPayload["experience"]>; label: string; years: string }[] = [
  { key: "junior", label: "Junior", years: "0–2 y" },
  { key: "intermediate", label: "Intermédiaire", years: "3–5 y" },
  { key: "senior", label: "Senior", years: "6+ y" },
];

const CONTRACTS: { key: PredictPayload["contract"]; label: string }[] = [
  { key: "cdi", label: "CDI" },
  { key: "freelance", label: "Freelance" },
  { key: "cdd", label: "CDD" },
  { key: "alternance", label: "Alternance" },
];

const SUGGESTIONS = ["React", "TypeScript", "Python", "FastAPI", "Docker", "SQL", "AWS", "Node.js"];

// Déduit le marché à partir de la ville sélectionnée -- pas de toggle
// séparé, la ville seule détermine "tunisia" / "france" / "remote".
function getMarketFromCity(city: string): PredictPayload["market"] {
  const frCities = ["Paris", "Lyon", "Bordeaux", "Toulouse", "Nantes"];
  const tnCities = ["Sousse", "Tunis"];

  if (city === "Remote") return "remote";
  if (frCities.includes(city)) return "france";
  if (tnCities.includes(city)) return "tunisia";
  return "france";
}

interface Props {
  onSubmit: (payload: PredictPayload) => void;
  loading: boolean;
}

export function PredictionForm({ onSubmit, loading }: Props) {
  const [city, setCity] = useState("Paris");
  const [experience, setExperience] = useState<NonNullable<PredictPayload["experience"]>>("intermediate");
  const [contract, setContract] = useState<PredictPayload["contract"]>("cdi");
  const [technologies, setTechnologies] = useState<string[]>(["React", "TypeScript"]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();

    const market = getMarketFromCity(city);
    // On ne garde experience que pour la France -- pas de champ fiable
    // exploitable côté Tunisie/Remote pour ce niveau de granularité.
    const isFranceCity = market === "france";

    const basePayload: PredictPayload = {
      city,
      contract,
      technologies,
      market,
    };

    const payload = isFranceCity
      ? { ...basePayload, experience } // France -> on envoie l'expérience
      : basePayload;                   // Tunisie / Remote -> sans expérience

    onSubmit(payload);
  };

  return (
    <form onSubmit={submit} className="glass relative overflow-hidden rounded-3xl p-6 md:p-8">
      <div className="pointer-events-none absolute -top-24 -right-24 h-64 w-64 rounded-full bg-gradient-to-br from-indigo-500/30 to-violet-500/10 blur-3xl" />

      <div className="relative space-y-6">
        <div className="flex items-center gap-2">
          <span className="glass-inset inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            <Sparkles className="h-3 w-3 text-primary" />
            AI Model v2.4
          </span>
        </div>

        <div>
          <h2 className="font-display text-2xl font-bold">Ton profil</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Renseigne ton profil pour analyser ton salaire, ta couverture du marché et débloquer tes recommandations de carrière.
          </p>
        </div>

        {/* City */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Ville
          </label>
          <div className="glass-inset flex items-center gap-2 rounded-xl px-3 py-2.5 transition-all focus-within:ring-2 focus-within:ring-primary/60">
            <MapPin className="h-4 w-4 text-primary" />
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="w-full appearance-none bg-transparent text-sm outline-none"
            >
              {CITIES.map((c) => (
                <option key={c} value={c} className="bg-background text-foreground">
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Experience segmented */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Niveau d'expérience
          </label>
          <div className="glass-inset relative grid grid-cols-3 gap-1 rounded-xl p-1">
            {EXPERIENCE.map((exp) => {
              const active = experience === exp.key;
              return (
                <button
                  key={exp.key}
                  type="button"
                  onClick={() => setExperience(exp.key)}
                  className={`relative flex flex-col items-center rounded-lg px-2 py-2 text-sm font-medium transition-all ${
                    active
                      ? "gradient-bg text-white shadow-lg shadow-violet-500/30"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <span>{exp.label}</span>
                  <span className={`text-[10px] ${active ? "text-white/80" : "text-muted-foreground/70"}`}>
                    {exp.years}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Contract */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Type de contrat
          </label>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {CONTRACTS.map((c) => {
              const active = contract === c.key;
              return (
                <button
                  key={c.key}
                  type="button"
                  onClick={() => setContract(c.key)}
                  className={`glass-inset flex items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-sm font-medium transition-all ${
                    active
                      ? "border-primary/60 bg-primary/10 text-foreground ring-1 ring-primary/40"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Briefcase className={`h-3.5 w-3.5 ${active ? "text-primary" : ""}`} />
                  {c.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tech */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Technologies
          </label>
          <TagInput tags={technologies} onChange={setTechnologies} suggestions={SUGGESTIONS} />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-glow btn-glow-hover group relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-2xl py-3.5 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-70"
        >
          <Zap className={`h-4 w-4 transition-transform ${loading ? "" : "group-hover:translate-x-0.5"}`} />
          <span>{loading ? "Analyse en cours…" : "Générer mon rapport de marché"}</span>
          <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/25 to-transparent transition-transform duration-1000 group-hover:translate-x-full" />
        </button>
      </div>
    </form>
  );
}