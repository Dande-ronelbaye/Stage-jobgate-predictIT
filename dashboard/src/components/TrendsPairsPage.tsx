import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import * as d3 from "d3";

/**
 * ─────────────────────────────────────────────────────────────────────────
 * ADAPTATION NOTE
 * Forme réelle confirmée côté backend (main.py, étape 1) :
 *
 * GET /api/analytics/trends?market=&n_periods=&top_n=
 * { periods_total: number, skills: [{ skill: string, points: [{ period: string, count: number }] }] }
 *
 * GET /api/analytics/pairs?market=&min_cooccurrence=&top_n=
 * { total_offers: number, pairs: [{ skillA, skillB, coOccurrence, lift }] }
 *
 * ⚠️ Pas de vraie date dans JobModel : "period" est un proxy basé sur
 * l'ordre d'insertion (id croissant), pas un mois calendaire. D'où
 * "Période 1, 2, 3…" plutôt que des dates dans toute l'UI ci-dessous.
 * ─────────────────────────────────────────────────────────────────────────
 */

interface TrendPoint {
  period: string; // ex. "Période 1" — proxy id, pas une vraie date
  count: number;
}

interface SkillTrend {
  skill: string;
  points: TrendPoint[];
}

interface SkillPair {
  skillA: string;
  skillB: string;
  coOccurrence: number;
  lift: number;
}

function adaptTrendsResponse(raw: any): SkillTrend[] {
  const list = raw?.skills ?? [];
  return list.map((s: any) => ({
    skill: s.skill,
    points: (s.points ?? []).map((p: any) => ({
      period: p.period,
      count: p.count ?? 0,
    })),
  }));
}

function adaptPairsResponse(raw: any): SkillPair[] {
  const list = raw?.pairs ?? [];
  return list.map((p: any) => ({
    skillA: p.skillA,
    skillB: p.skillB,
    coOccurrence: p.coOccurrence ?? 0,
    lift: p.lift ?? 0,
  }));
}

const WINDOW_OPTIONS = [
  { label: "3 périodes", value: 3 },
  { label: "6 périodes", value: 6 },
  { label: "12 périodes", value: 12 },
];

const PALETTE = [
  "#7dd3fc", "#c4b5fd", "#f9a8d4", "#86efac", "#fcd34d",
  "#fda4af", "#67e8f9", "#a5b4fc", "#fdba74", "#5eead4",
];

function slope(points: TrendPoint[]): number {
  if (points.length < 2) return 0;
  const n = points.length;
  const xs = points.map((_, i) => i);
  const ys = points.map((p) => p.count);
  const xMean = xs.reduce((a, b) => a + b, 0) / n;
  const yMean = ys.reduce((a, b) => a + b, 0) / n;
  const num = xs.reduce((s, x, i) => s + (x - xMean) * (ys[i] - yMean), 0);
  const den = xs.reduce((s, x) => s + (x - xMean) ** 2, 0);
  return den === 0 ? 0 : num / den;
}

// Vite expose les variables préfixées VITE_ via import.meta.env.
// Ajoute VITE_API_URL=http://localhost:8000 dans ton fichier .env si ce n'est pas déjà fait.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function TrendsPairsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trends, setTrends] = useState<SkillTrend[]>([]);
  const [pairs, setPairs] = useState<SkillPair[]>([]);
  const [windowPeriods, setWindowPeriods] = useState(6);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [pairsView, setPairsView] = useState<"table" | "network">("table");
  const [pairsSearch, setPairsSearch] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [trendsRes, pairsRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/api/analytics/trends`, {
            params: { market: "tunisia", n_periods: 12, top_n: 10 },
          }),
          axios.get(`${API_BASE_URL}/api/analytics/pairs`, {
            params: { market: "tunisia", min_cooccurrence: 3, top_n: 50 },
          }),
        ]);

        if (cancelled) return;

        const t = adaptTrendsResponse(trendsRes.data);
        const p = adaptPairsResponse(pairsRes.data);

        setTrends(t);
        setPairs(p);
        setSelectedSkills(
          [...t]
            .sort((a, b) => (b.points.at(-1)?.count ?? 0) - (a.points.at(-1)?.count ?? 0))
            .slice(0, 6)
            .map((s) => s.skill)
        );
      } catch (err) {
        if (!cancelled) {
          console.error(err);
          setError(
            "Impossible de charger les analyses. Vérifie que l'API tourne sur " + API_BASE_URL
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  // Découpe chaque série sur la fenêtre temporelle globale
  const windowedTrends = useMemo(() => {
    return trends.map((s) => ({
      ...s,
      points: s.points.slice(-windowPeriods),
    }));
  }, [trends, windowPeriods]);

  const rankedBySlope = useMemo(() => {
    return [...windowedTrends]
      .map((s) => ({ skill: s.skill, slope: slope(s.points) }))
      .sort((a, b) => b.slope - a.slope);
  }, [windowedTrends]);

  const topGrowing = rankedBySlope[0];
  const topDeclining = rankedBySlope.at(-1);

  const chartData = useMemo(() => {
    const periods = windowedTrends[0]?.points.map((p) => p.period) ?? [];
    return periods.map((period, i) => {
      const row: Record<string, string | number> = { period };
      windowedTrends.forEach((s) => {
        if (selectedSkills.includes(s.skill)) {
          row[s.skill] = s.points[i]?.count ?? 0;
        }
      });
      return row;
    });
  }, [windowedTrends, selectedSkills]);

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  };

  const filteredPairs = useMemo(() => {
    const q = pairsSearch.trim().toLowerCase();
    return [...pairs]
      .filter(
        (p) =>
          !q ||
          p.skillA.toLowerCase().includes(q) ||
          p.skillB.toLowerCase().includes(q)
      )
      .sort((a, b) => b.lift - a.lift);
  }, [pairs, pairsSearch]);

  const maxLift = Math.max(...pairs.map((p) => p.lift), 1);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground text-sm">Chargement des analyses…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-6">
        <div className="text-rose-300 text-sm text-center max-w-md">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-6 space-y-6">
      {/* Header + sélecteur global */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Tendances &amp; Associations de compétences
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Évolution des compétences les plus demandées (par période) et leurs associations fréquentes.
          </p>
        </div>
        <div className="flex glass rounded-xl p-1">
          {WINDOW_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setWindowPeriods(opt.value)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                windowPeriods === opt.value
                  ? "bg-sky-500/20 text-sky-300 border border-sky-400/30"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Cartes insight */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="glass rounded-2xl p-5">
          <div className="text-xs uppercase tracking-wide text-emerald-400/80 mb-1">
            🔥 Croissance la plus forte
          </div>
          <div className="text-xl font-semibold">{topGrowing?.skill ?? "—"}</div>
          <div className="text-muted-foreground text-sm mt-1">
            sur les {windowPeriods} dernières périodes
          </div>
        </div>
        <div className="glass rounded-2xl p-5">
          <div className="text-xs uppercase tracking-wide text-rose-400/80 mb-1">
            📉 En déclin
          </div>
          <div className="text-xl font-semibold">{topDeclining?.skill ?? "—"}</div>
          <div className="text-muted-foreground text-sm mt-1">
            sur les {windowPeriods} dernières périodes
          </div>
        </div>
      </div>

      {/* Bloc Trends */}
      <div className="glass rounded-2xl p-5">
        <h2 className="text-lg font-medium mb-3">Évolution des compétences</h2>

        <div className="flex flex-wrap gap-2 mb-4">
          {trends.map((s, i) => {
            const active = selectedSkills.includes(s.skill);
            return (
              <button
                key={s.skill}
                onClick={() => toggleSkill(s.skill)}
                className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                  active
                    ? "border-transparent text-slate-900"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
                style={active ? { backgroundColor: PALETTE[i % PALETTE.length] } : undefined}
              >
                {s.skill}
              </button>
            );
          })}
        </div>

        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis dataKey="period" stroke="#64748b" fontSize={12} />
            <YAxis stroke="#64748b" fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            {trends
              .filter((s) => selectedSkills.includes(s.skill))
              .map((s, i) => (
                <Line
                  key={s.skill}
                  type="monotone"
                  dataKey={s.skill}
                  stroke={PALETTE[trends.findIndex((t) => t.skill === s.skill) % PALETTE.length]}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Bloc Pairs */}
      <div className="glass rounded-2xl p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="text-lg font-medium">Compétences associées</h2>
          <div className="flex items-center gap-3">
            <input
              value={pairsSearch}
              onChange={(e) => setPairsSearch(e.target.value)}
              placeholder="Filtrer une compétence…"
              className="glass rounded-lg px-3 py-1.5 text-sm placeholder-muted-foreground focus:outline-none focus:border-sky-400/40"
            />
            <div className="flex glass rounded-lg p-1">
              {(["table", "network"] as const).map((v) => (
                <button
                  key={v}
                  onClick={() => setPairsView(v)}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    pairsView === v
                      ? "bg-sky-500/20 text-sky-300"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {v === "table" ? "Tableau" : "Graphe"}
                </button>
              ))}
            </div>
          </div>
        </div>

        {pairsView === "table" ? (
          <PairsTable pairs={filteredPairs} maxLift={maxLift} />
        ) : (
          <PairsNetwork pairs={filteredPairs} />
        )}
      </div>
    </div>
  );
}

function PairsTable({ pairs, maxLift }: { pairs: SkillPair[]; maxLift: number }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-muted-foreground border-b border-border">
            <th className="py-2 pr-4 font-normal">Paire</th>
            <th className="py-2 pr-4 font-normal">Co-occurrences</th>
            <th className="py-2 pr-4 font-normal">Lift</th>
          </tr>
        </thead>
        <tbody>
          {pairs.slice(0, 30).map((p, i) => (
            <tr key={`${p.skillA}-${p.skillB}`} className="border-b border-border/50">
              <td className="py-2 pr-4">
                <span className="text-foreground">{p.skillA}</span>
                <span className="text-muted-foreground mx-1.5">×</span>
                <span className="text-foreground">{p.skillB}</span>
              </td>
              <td className="py-2 pr-4 text-muted-foreground">{p.coOccurrence}</td>
              <td className="py-2 pr-4">
                <div className="flex items-center gap-2">
                  <div className="w-24 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-sky-400/70 rounded-full"
                      style={{ width: `${(p.lift / maxLift) * 100}%` }}
                    />
                  </div>
                  <span className="text-foreground tabular-nums">{p.lift.toFixed(2)}</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {pairs.length === 0 && (
        <div className="text-muted-foreground text-sm py-8 text-center">Aucune paire trouvée.</div>
      )}
    </div>
  );
}

function PairsNetwork({ pairs }: { pairs: SkillPair[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const width = 760;
  const height = 420;

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const topPairs = pairs.slice(0, 40);
    const nodeNames = Array.from(
      new Set(topPairs.flatMap((p) => [p.skillA, p.skillB]))
    );
    const nodes = nodeNames.map((name) => ({
      id: name,
      degree: topPairs.filter((p) => p.skillA === name || p.skillB === name).length,
    }));
    const links = topPairs.map((p) => ({
      source: p.skillA,
      target: p.skillB,
      lift: p.lift,
    }));

    const simulation = d3
      .forceSimulation(nodes as any)
      .force(
        "link",
        d3
          .forceLink(links as any)
          .id((d: any) => d.id)
          .distance(90)
      )
      .force("charge", d3.forceManyBody().strength(-180))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(28));

    const link = svg
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "rgba(125, 211, 252, 0.35)")
      .attr("stroke-width", (d: any) => Math.max(1, d.lift));

    const node = svg
      .append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", (d: any) => 8 + d.degree * 2)
      .attr("fill", "#7dd3fc")
      .attr("fill-opacity", 0.85)
      .attr("stroke", "#0f172a")
      .attr("stroke-width", 1.5)
      .call(
        d3
          .drag<SVGCircleElement, any>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    const label = svg
      .append("g")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .text((d: any) => d.id)
      .attr("font-size", 11)
      .attr("fill", "#cbd5e1")
      .attr("text-anchor", "middle")
      .attr("dy", -14);

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);
      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
      label.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
    });

    return () => {
      simulation.stop();
    };
  }, [pairs]);

  return (
    <div className="overflow-x-auto">
      <svg ref={svgRef} width={width} height={height} className="mx-auto" />
      <p className="text-muted-foreground text-xs text-center mt-2">
        Taille du nœud = nombre d'associations · Épaisseur du lien = lift · glisser pour réorganiser
      </p>
    </div>
  );
}