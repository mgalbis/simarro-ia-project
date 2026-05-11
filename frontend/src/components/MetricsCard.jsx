import React from "react";

export default function MetricsCard({
  title = "MÉTRICAS DE MODELOS",
  modelName = "Clasificador v2.1",
  status = "ACTIVE",
  metrics = [
    { label: "Exactitud", value: 94 },
    { label: "Precisión", value: 89 },
    { label: "F1-Score", value: 92 }
  ],
}) {
  return (
    <div className="bg-black/30 border border-qa-border-glow rounded-xl p-4 shadow-[inset_0_0_15px_rgba(142,53,255,0.1)]">
      {/* TÍTULO */}
      <div className="flex items-center gap-2 text-qa-purple-light font-black text-[14px] tracking-wider uppercase mb-3">
        <span className="text-qa-magenta text-lg">⌁</span>
        {title}
      </div>

      {/* INFO DEL MODELO */}
      <div className="flex justify-between items-center mb-5 px-1">
        <div className="text-[13px] font-extrabold text-qa-purple-light tracking-tight">
          Modelo: <span className="text-white">{modelName}</span>
        </div>

        <div className="flex items-center gap-1.5 text-[10px] font-black tracking-widest text-qa-green">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-qa-green opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-qa-green"></span>
          </span>
          {status}
        </div>
      </div>

      {/* LISTA DE MÉTRICAS */}
      <div className="space-y-4">
        {metrics.map((m, index) => (
          <MetricRow
            key={index}
            label={m.label}
            value={m.value}
          />
        ))}
      </div>
    </div>
  );
}

/* ---------- SUBCOMPONENTE: FILA DE MÉTRICA ---------- */

function MetricRow({ label, value }) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between text-[11px] font-bold uppercase tracking-tighter text-qa-muted">
        <span>{label}</span>
        <span className="text-white font-black">{value}%</span>
      </div>

      <div className="flex items-center gap-3">
        {/* TRACK (Carril de la barra) */}
        <div className="flex-1 h-2 bg-slate-900/80 rounded-full border border-white/5 overflow-hidden">
          {/* FILL (Progreso) */}
          <div
            className="h-full bg-gradient-to-r from-qa-purple via-qa-purple-light to-qa-magenta shadow-[0_0_10px_rgba(142,53,255,0.6)] transition-all duration-1000 ease-out"
            style={{ width: `${value}%` }}
          />
        </div>
      </div>
    </div>
  );
}