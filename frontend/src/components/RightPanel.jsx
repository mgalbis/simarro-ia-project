import React from "react";
import HistoryCard from "./HistoryCard";
import MetricsCard from "./MetricsCard";

export default function RightPanel({
  history = [],
  lastReport = null,
}) {

  const getStatusClass = (status) => {
    switch (status?.toUpperCase()) {
      case "SUCCESS":
      case "PASS":
        return "text-qa-green font-black";
      case "WARN":
      case "WARNING":
        return "text-yellow-400 font-black";
      case "FAIL":
      case "ERROR":
        return "text-qa-magenta font-black";
      default:
        return "text-qa-muted font-black";
    }
  };

  return (
    <aside className="bg-qa-panel border border-qa-border rounded-[22px] backdrop-blur-xl shadow-[0_0_25px_rgba(142,53,255,0.25)] p-4 flex flex-col gap-4 h-full overflow-y-auto">
      
      {/* SECCIÓN 1: HISTORIAL (Últimas ejecuciones) */}
      <div className="bg-[#0c0d21]/40 border border-qa-border-glow rounded-xl overflow-hidden">
        <HistoryCard history={history} />
      </div>

      {/* SECCIÓN 2: ÚLTIMA EJECUCIÓN */}
      <div className="bg-[#0c0d21]/40 border border-qa-border-glow rounded-xl p-4 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-qa-purple-light font-black text-[13px] tracking-wider uppercase">
            <span className="text-lg">▣</span> ÚLTIMA EJECUCIÓN
          </div>
        </div>

        {!lastReport ? (
          <p className="text-[11px] text-qa-muted italic leading-relaxed">
            Todavía no hay resultados. Carga un CSV y solicita una validación para ver el reporte.
          </p>
        ) : (
          <div className="space-y-3">
            <div className="flex justify-between items-end border-b border-qa-border/30 pb-2">
              <div className="text-[10px] text-qa-muted uppercase font-bold tracking-tighter">
                ID: {lastReport.execution_id || "N/A"}
              </div>
              <div className="text-[12px] font-bold text-white">
                Global: <span className={getStatusClass(lastReport.global_status)}>{lastReport.global_status}</span>
              </div>
            </div>

            <div className="flex flex-col gap-2 max-h-[150px] overflow-y-auto pr-1">
              {lastReport.results?.map((r, i) => (
                <div key={i} className="flex justify-between items-center text-[10px] bg-black/30 p-2 rounded-lg border border-white/5 hover:border-qa-purple/30 transition-colors">
                  <div className="flex flex-col">
                    <span className="text-white/90 font-bold">{r.name}</span>
                    {r.details && <span className="text-[9px] text-qa-muted">{r.details}</span>}
                  </div>
                  <span className={getStatusClass(r.status)}>{r.status}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* SECCIÓN 3: MÉTRICAS (Dinámicas) */}
      <MetricsCard
        modelName={lastReport ? "Análisis de Datos" : "Sistema Inactivo"}
        status={lastReport ? "COMPLETED" : "WAITING"}
        metrics={lastReport?.metrics ? lastReport.metrics : [
          { label: "Nulos", value: 0 },
          { label: "Duplicados", value: 0 },
          { label: "Outliers", value: 0 },
          { label: "Consistencia", value: 0 },
        ]}
      />

      {/* LOGO */}
      <div className="mt-auto pt-6 flex justify-center border-t border-qa-border/20">
        <img 
          src="/QABotSimarro.png" 
          alt="IES Lluis Simarro" 
          className="w-[240px] md:w-[280px] opacity-90 filter grayscale brightness-125 contrast-110 drop-shadow-[0_0_12px_rgba(142,53,255,0.5)] transition-all hover:scale-105"
        />
      </div>
    </aside>
  );
}