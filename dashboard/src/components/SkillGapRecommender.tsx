import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchGapAnalysis } from '@/lib/api';

export function SkillGapRecommender() {
  const [techInput, setTechInput] = useState<string>('Python, React, Django');
  const [activeTechs, setActiveTechs] = useState<string[]>(['Python', 'React', 'Django']);

  const { data, isLoading } = useQuery({
    queryKey: ['gapAnalysis', activeTechs],
    queryFn: () => fetchGapAnalysis(activeTechs),
    enabled: activeTechs.length > 0,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const list = techInput.split(',').map((t) => t.trim()).filter(Boolean);
    if (list.length > 0) {
      setActiveTechs(list);
    }
  };

  return (
    <div className="w-full bg-card/80 backdrop-blur-xl border border-border p-6 rounded-3xl shadow-2xl">
      <h3 className="text-xl font-bold text-foreground mb-2 flex items-center gap-2">
        🎯 Analyseur de Couverture & Recommandations
      </h3>
      <p className="text-xs text-muted-foreground mb-6">
        Testez votre stack technique actuelle pour découvrir votre taux de qualification sur le marché et les compétences prioritaires à apprendre.
      </p>

      {/* Formulaire de saisie des technos */}
      <form onSubmit={handleSearch} className="flex gap-3 mb-6">
        <input
          type="text"
          value={techInput}
          onChange={(e) => setTechInput(e.target.value)}
          placeholder="Ex: Python, React, SQL"
          className="flex-1 bg-secondary/50 border border-border/60 rounded-xl px-4 py-2 text-sm text-foreground focus:outline-none focus:border-primary"
        />
        <button
          type="submit"
          className="bg-primary text-primary-foreground font-semibold px-5 py-2 rounded-xl text-sm hover:opacity-90 transition-all"
        >
          Analyser
        </button>
      </form>

      {/* Affichage des résultats */}
      {isLoading ? (
        <p className="text-sm text-muted-foreground text-center py-8">Analyse de la base d'offres...</p>
      ) : data ? (
        <div className="space-y-6">
          {/* Métrique principale */}
          <div className="bg-secondary/30 p-4 rounded-2xl border border-border/40 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground uppercase font-semibold">Taux de qualification actuel</p>
              <h4 className="text-2xl font-extrabold text-primary">{data.current_qualifying_pct}% des offres</h4>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Offres éligibles</p>
              <p className="text-lg font-bold text-foreground">{data.current_qualifying_count} / {data.total_offers}</p>
            </div>
          </div>

          {/* Recommandations */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3">Compétences prioritaires à apprendre :</h4>
            <div className="space-y-2">
              {data.recommendations.map((rec, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-xl bg-secondary/20 hover:bg-secondary/40 border border-border/30 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-primary/20 text-primary text-xs font-bold flex items-center justify-center">
                      +{index + 1}
                    </span>
                    <span className="font-semibold text-foreground text-sm">{rec.skill}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-emerald-400 font-medium">
                      +{rec.unlocked_offers_count} offres débloquées
                    </span>
                    <p className="text-[10px] text-muted-foreground">Couverture potentielle : {rec.new_coverage_pct}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}