import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { fetchAnalyticsStats } from '@/lib/api';

export function MarketDashboard() {
  const [activeMarket, setActiveMarket] = useState<'tunisia' | 'france'>('tunisia');

  const { data, isLoading } = useQuery({
    queryKey: ['analyticsStats', activeMarket],
    queryFn: () => fetchAnalyticsStats(activeMarket),
  });

  const kpis = data?.kpis || {
    total_offers: 1967,
    sources_count: 3,
    duplicates_removed_pct: 89,
    model_accuracy_pct: 86,
  };

  // Sécurité : s'assure qu'on a toujours un tableau valide
  const skillsData = data?.skills && data.skills.length > 0 ? data.skills : [
    { name: 'Python', count: 312 },
    { name: 'JavaScript', count: 288 },
    { name: 'Java', count: 251 },
    { name: 'SQL', count: 229 },
    { name: 'Angular', count: 204 },
    { name: 'React', count: 181 },
    { name: '.NET', count: 158 },
    { name: 'Docker', count: 126 },
  ];

  return (
    <div className="w-full rounded-3xl bg-card/80 backdrop-blur-xl border border-border p-6 md:p-8 shadow-2xl font-sans">

      {/* En-tête */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <span className="glass inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs mb-2">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-primary" />
            </span>
            <span className="text-muted-foreground font-medium uppercase tracking-wider">Market Intelligence</span>
          </span>
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            Vue d'ensemble du marché IT
          </h2>
        </div>
      </div>

      {/* 1. KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-secondary/40 p-5 rounded-2xl border border-border/50 hover:border-primary/30 transition-all">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">Offres analysées</p>
          <h3 className="text-3xl font-extrabold text-foreground">{kpis.total_offers.toLocaleString()}</h3>
        </div>

        <div className="bg-secondary/40 p-5 rounded-2xl border border-border/50 hover:border-primary/30 transition-all">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">Sources actives</p>
          <h3 className="text-3xl font-extrabold text-foreground">{kpis.sources_count}</h3>
        </div>

        <div className="bg-secondary/40 p-5 rounded-2xl border border-border/50 hover:border-primary/30 transition-all">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">Doublons éliminés</p>
          <h3 className="text-3xl font-extrabold text-foreground">{kpis.duplicates_removed_pct}%</h3>
        </div>

        <div className="bg-secondary/40 p-5 rounded-2xl border border-border/50 hover:border-primary/30 transition-all">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">Précision modèle</p>
          <h3 className="text-3xl font-extrabold gradient-text">
            {kpis.model_accuracy_pct}%
          </h3>
        </div>
      </div>

      {/* 2. Boutons de choix du marché */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <button
          onClick={() => setActiveMarket('tunisia')}
          className={`py-3.5 px-6 rounded-2xl text-sm font-semibold transition-all duration-300 ${
            activeMarket === 'tunisia'
              ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-600/30 border border-violet-400/30'
              : 'bg-secondary/50 text-muted-foreground hover:text-foreground border border-border/50'
          }`}
        >
          🇹🇳 Marché Tunisie (Keejob + Tunisie Travail)
        </button>

        <button
          onClick={() => setActiveMarket('france')}
          className={`py-3.5 px-6 rounded-2xl text-sm font-semibold transition-all duration-300 ${
            activeMarket === 'france'
              ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-600/30 border border-violet-400/30'
              : 'bg-secondary/50 text-muted-foreground hover:text-foreground border border-border/50'
          }`}
        >
          🇫🇷 Marché France (Welcome to the Jungle)
        </button>
      </div>

      {/* 3. Diagramme Recharts */}
      <div className="bg-secondary/30 p-6 rounded-2xl border border-border/50">
        <h4 className="text-muted-foreground font-semibold mb-6 text-sm tracking-wide flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          Compétences les plus demandées — {activeMarket === 'tunisia' ? 'Tunisie' : 'France'}
        </h4>

        {/* Min-height explicite fixée pour forcer Recharts à calculer le conteneur */}
        <div className="h-[380px] min-h-[380px] w-full relative">
          {isLoading ? (
            <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
              Chargement des insights marché...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={skillsData}
                margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
              >
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                </defs>

                <CartesianGrid horizontal={false} stroke="rgba(255, 255, 255, 0.05)" />
                <XAxis
                  type="number"
                  stroke="#475569"
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  axisLine={{ stroke: 'rgba(255, 255, 255, 0.05)' }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#475569"
                  tick={{ fill: '#cbd5e1', fontSize: 13, fontWeight: 500 }}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(255, 255, 255, 0.05)' }}
                  width={100}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0d0f1d',
                    borderColor: 'rgba(139, 92, 246, 0.3)',
                    borderRadius: '12px',
                    color: '#fff',
                    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)'
                  }}
                  cursor={{ fill: 'rgba(255, 255, 255, 0.03)' }}
                />
                <Bar
                  dataKey="count"
                  fill="url(#barGradient)"
                  radius={[0, 6, 6, 0]}
                  barSize={22}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

    </div>
  );
}