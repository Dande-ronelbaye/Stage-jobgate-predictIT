import { Activity, Sparkles, Target, TrendingUp, Zap } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PredictResponse, GapAnalysisResponse } from "@/lib/api";
import { AnimatedCounter } from "./AnimatedCounter";

type Status = "idle" | "loading" | "success";

interface Props {
  status: Status;
  data: PredictResponse | null;
  gapData: GapAnalysisResponse | null; // 👈 PROP GAP ANALYSIS
}

export function ResultsPanel({ status, data, gapData }: Props) {
  if (status === "idle") return <IdleState />;
  if (status === "loading") return <LoadingState />;
  // Avant : `if (!data) return <IdleState />` masquait TOUT (y compris le
  // gap analysis) dès que data était null -- ce qui arrive maintenant
  // volontairement pour la Tunisie/certains cas Remote (predictSalary non
  // appelé ou en échec silencieux). On affiche les résultats dès que
  // gapData OU data est disponible.
  if (!data && !gapData) return <IdleState />;
  return <SuccessState data={data} gapData={gapData} />;
}

function IdleState() {
  return (
    <div className="glass relative flex min-h-[560px] flex-col items-center justify-center overflow-hidden rounded-3xl p-8 text-center">
      <div className="pointer-events-none absolute inset-0 grid-overlay opacity-60" />

      <div className="relative">
        <div className="relative float-slow">
          <div className="gradient-bg mx-auto grid h-24 w-24 place-items-center rounded-3xl shadow-2xl shadow-violet-500/40">
            <Sparkles className="h-10 w-10 text-white" />
          </div>
          <div className="absolute -inset-4 -z-10 rounded-full bg-gradient-to-br from-indigo-500/30 to-fuchsia-500/20 blur-2xl" />
        </div>

        <h3 className="mt-8 font-display text-3xl font-bold">
          Découvre <span className="gradient-text">ton positionnement réel</span> ?
        </h3>
        <p className="mx-auto mt-3 max-w-sm text-sm text-muted-foreground">
          Remplis le formulaire pour obtenir ton taux de qualification sur le marché et les compétences clés à apprendre.
        </p>
        <div className="mt-8 grid grid-cols-3 gap-3">
          {[
            { icon: TrendingUp, label: "Positionnement prédit" },
            { icon: Target, label: "🎯 Gap Analysis & Couverture" },
            { icon: Zap, label: "💡 Compétences à impact" },
          ].map(({ icon: Icon, label }) => (
            <div key={label} className="glass-inset rounded-2xl p-3 text-xs">
              <Icon className="mx-auto h-4 w-4 text-primary" />
              <div className="mt-1 text-[11px] text-muted-foreground">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="glass relative flex min-h-[560px] flex-col gap-6 overflow-hidden rounded-3xl p-6 md:p-8">
      <div className="flex items-center gap-3">
        <div className="pulse-ring h-2 w-2 rounded-full bg-primary" />
        <span className="text-xs uppercase tracking-widest text-muted-foreground">
          Calcul du positionnement & Gap Analysis…
        </span>
      </div>

      <div className="space-y-3">
        <div className="skeleton-shimmer h-4 w-32 rounded-md" />
        <div className="skeleton-shimmer h-16 w-2/3 rounded-xl" />
        <div className="skeleton-shimmer h-3 w-40 rounded-md" />
      </div>

      <div className="skeleton-shimmer h-4 rounded-full" />

      <div className="space-y-3">
        <div className="skeleton-shimmer h-12 w-full rounded-2xl" />
        <div className="skeleton-shimmer h-12 w-full rounded-2xl" />
        <div className="skeleton-shimmer h-12 w-full rounded-2xl" />
      </div>
    </div>
  );
}

/* --------------------------------- SUCCESS --------------------------------- */

function SuccessState({
  data,
  gapData,
}: {
  data: PredictResponse | null;
  gapData: GapAnalysisResponse | null;
}) {
  return (
    <div className="glass relative overflow-hidden rounded-3xl p-6 md:p-8">
      <div className="pointer-events-none absolute -top-32 -right-24 h-72 w-72 rounded-full bg-gradient-to-br from-indigo-500/25 via-violet-500/20 to-fuchsia-500/10 blur-3xl" />

      <div className="relative space-y-6">
        {/* BLOC 1 (PRINCIPAL) : GAP ANALYSIS & COMPÉTENCES À IMPACT */}
        {gapData && (
          <div className="glass-inset rounded-2xl p-5 border border-border/50 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                <h4 className="text-sm font-semibold tracking-wide uppercase text-foreground">
                  Compétences à impact du profil
                </h4>
              </div>

              <span className="rounded-full bg-primary/10 border border-primary/20 px-3 py-1 text-xs font-bold text-primary">
                Couverture : {gapData.current_qualifying_pct}%
              </span>
            </div>

            <p className="text-xs text-muted-foreground">
              Vous qualifiez pour{" "}
              <strong className="text-foreground font-semibold">
                {gapData.current_qualifying_count}
              </strong>{" "}
              sur{" "}
              <strong className="text-foreground font-semibold">
                {gapData.total_offers}
              </strong>{" "}
              offres. Voici les compétences prioritaires à apprendre :
            </p>

            {/* LISTE ACTIONNABLE DE RECOMMANDATIONS */}
            <div className="space-y-2">
              {gapData.recommendations.map((rec, i) => (
                <div
                  key={i}
                  className="glass flex items-center justify-between p-3 rounded-xl border border-border/40 hover:border-primary/40 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary/20 text-[11px] font-bold text-primary">
                      +{i + 1}
                    </span>
                    <div>
                      <span className="text-xs font-bold text-foreground">
                        {rec.skill}
                      </span>
                      <span className="block text-[10px] text-muted-foreground">
                        Débloque{" "}
                        <span className="text-emerald-400 font-medium">
                          +{rec.unlocked_offers_count} offres
                        </span>
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs font-black gradient-text">
                      {rec.new_coverage_pct}%
                    </span>
                    <span className="block text-[9px] text-muted-foreground">
                      couverture
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* BLOC 2 (SECONDAIRE) : SALAIRE -- absent pour la Tunisie et si
            predictSalary échoue (Remote), grâce au garde-fou dans index.tsx */}
        {data && (
          <>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  Salaire prédit annuel
                </p>
                <h2 className="font-display text-5xl font-black leading-none md:text-6xl">
                  <span className="gradient-text">
                    <AnimatedCounter value={data.salary} />
                  </span>
                  <span className="ml-2 text-2xl text-muted-foreground">€ / an</span>
                </h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Médiane marché :{" "}
                  <span className="font-semibold text-foreground">
                    {data.marketMedian.toLocaleString("fr-FR")} €
                  </span>
                  {" · "}
                  Fourchette : {data.marketMin.toLocaleString("fr-FR")}–
                  {data.marketMax.toLocaleString("fr-FR")} €
                </p>
              </div>
              <div className="glass-inset hidden flex-col items-center rounded-2xl px-4 py-3 md:flex">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
                  Percentile
                </span>
                <span className="gradient-text font-display text-3xl font-black">
                  {data.percentile}
                </span>
              </div>
            </div>

            <MarketGauge percentile={data.percentile} />

            {/* GRAPHIQUES VILLES & TENDANCES EN BAS */}
            <div className="grid gap-4 md:grid-cols-2 pt-2">
              <ChartCard title="Salaires par ville" subtitle="Comparatif pour ton profil">
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={data.cities} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="oklch(0.66 0.26 300)" />
                        <stop offset="100%" stopColor="oklch(0.52 0.24 275)" />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="city" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--muted-foreground)" fontSize={11} tickLine={false} axisLine={false}
                      tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
                    <Tooltip
                      cursor={{ fill: "color-mix(in oklab, var(--primary) 8%, transparent)" }}
                      contentStyle={{
                        background: "var(--popover)",
                        border: "1px solid var(--border)",
                        borderRadius: 12,
                        fontSize: 12,
                      }}
                      formatter={(v: number) => [`${v.toLocaleString("fr-FR")} €`, "Salaire"]}
                    />
                    <Bar dataKey="salary" fill="url(#barGrad)" radius={[8, 8, 4, 4]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Demande par techno" subtitle="Index de popularité (0–100)">
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart layout="vertical" data={data.techDemand} margin={{ top: 4, right: 12, left: 8, bottom: 0 }}>
                    <defs>
                      <linearGradient id="hbarGrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="oklch(0.52 0.24 275)" />
                        <stop offset="100%" stopColor="oklch(0.72 0.26 330)" />
                      </linearGradient>
                    </defs>
                    <CartesianGrid horizontal={false} stroke="var(--border)" strokeDasharray="3 3" />
                    <XAxis type="number" hide domain={[0, 100]} />
                    <YAxis
                      type="category"
                      dataKey="tech"
                      stroke="var(--muted-foreground)"
                      fontSize={11}
                      width={80}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      cursor={{ fill: "color-mix(in oklab, var(--primary) 8%, transparent)" }}
                      contentStyle={{
                        background: "var(--popover)",
                        border: "1px solid var(--border)",
                        borderRadius: 12,
                        fontSize: 12,
                      }}
                    />
                    <Bar dataKey="demand" radius={[4, 8, 8, 4]}>
                      {data.techDemand.map((_, i) => (
                        <Cell key={i} fill="url(#hbarGrad)" />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* --------------------------------- HELPERS --------------------------------- */

function MarketGauge({ percentile }: { percentile: number }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Position marché</span>
        <span className="font-semibold text-foreground">
          Top {100 - percentile}% des profils
        </span>
      </div>
      <div className="relative">
        <div
          className="h-3 w-full rounded-full"
          style={{
            background:
              "linear-gradient(90deg, oklch(0.7 0.18 145) 0%, oklch(0.82 0.17 90) 50%, oklch(0.65 0.24 25) 100%)",
          }}
        />
        <div
          className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 transition-all duration-1000"
          style={{ left: `${percentile}%` }}
        >
          <div className="relative">
            <div className="h-6 w-6 rounded-full bg-white ring-4 ring-primary shadow-lg shadow-violet-500/40" />
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-foreground px-2 py-0.5 text-[10px] font-bold text-background">
              {percentile}%
            </div>
          </div>
        </div>
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>Min marché</span>
        <span>Médiane</span>
        <span>Max marché</span>
      </div>
    </div>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="glass-inset rounded-2xl p-4">
      <div className="mb-2">
        <h4 className="text-sm font-semibold">{title}</h4>
        <p className="text-[11px] text-muted-foreground">{subtitle}</p>
      </div>
      {children}
    </div>
  );
}