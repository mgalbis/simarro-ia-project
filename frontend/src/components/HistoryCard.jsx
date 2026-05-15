import React from "react";

const STATUS_CONFIG = {
  PASS: {
    icon: "✓",
    iconColor: "text-qa-green",
    glow: "drop-shadow-[0_0_5px_rgba(0,255,133,0.5)]",
    badge: "bg-qa-green/10 text-qa-green border-qa-green/20",
    label: "Completado",
  },
  WARN: {
    icon: "⚠",
    iconColor: "text-yellow-400",
    glow: "drop-shadow-[0_0_5px_rgba(250,204,21,0.5)]",
    badge: "bg-yellow-400/10 text-yellow-400 border-yellow-400/20",
    label: "Advertencia",
  },
  FAIL: {
    icon: "✕",
    iconColor: "text-qa-magenta",
    glow: "drop-shadow-[0_0_5px_rgba(232,121,160,0.5)]",
    badge: "bg-qa-magenta/10 text-qa-magenta border-qa-magenta/20",
    label: "Fallido",
  },
};

export default function HistoryCard({
  title = "HISTORIAL DE PRUEBAS DE CALIDAD DE DATOS",
  history = [],
}) {
  return (
    <div className="flex flex-col h-full">
      {/* TÍTULO DEL PANEL */}
      <div className="flex items-center gap-2 text-qa-purple-light font-black text-[12px] tracking-wider uppercase p-4 pb-2">
        <span className="text-qa-magenta text-lg leading-none">▰</span> 
        {title}
      </div>

      {history.length === 0 ? (
        <div className="px-4 py-6 text-qa-muted text-[12px] text-center italic">
          No hay historial disponible.
        </div>
      ) : (
        <div className="flex flex-col gap-1 px-2 pb-4 overflow-y-auto max-h-[400px]">
          {history.map((item, index) => (
            <HistoryItem
              key={index}
              fileName={item.fileName || "Dataset"}
              date={item.date}
              status={item.status || "PASS"}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function HistoryItem({ fileName, date, status }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.PASS;

  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-black/20 border border-transparent hover:border-qa-border-glow transition-all group cursor-pointer">
      
      {/* ICONO DE BASE DE DATOS */}
      <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-qa-deep border border-qa-border-glow flex items-center justify-center shadow-[0_0_10px_rgba(142,53,255,0.2)] group-hover:shadow-[0_0_15px_rgba(142,53,255,0.4)]">
        <div className="w-5 h-3.5 border-2 border-qa-purple-light rounded-sm relative after:content-[''] after:absolute after:top-1 after:left-1 after:w-2 after:h-0.5 after:bg-qa-purple-light after:shadow-[0_3px_0] after:shadow-qa-purple-light"></div>
      </div>

      {/* CONTENIDO TEXTUAL */}
      <div className="flex-1 min-w-0">
        <div className="text-[13px] font-bold text-white truncate group-hover:text-qa-purple-light transition-colors">
          {fileName}
        </div>
        <div className="text-[10px] text-qa-muted flex items-center gap-2 mt-0.5">
          {date} 
          <span className={`px-1.5 py-0.5 rounded-md border ${config.badge} text-[9px] font-bold uppercase tracking-tighter`}>
            {config.label}
          </span>
        </div>
      </div>

      {/* ICONO DE ESTADO */}
      <div className={`font-bold text-sm ml-2 filter ${config.iconColor} ${config.glow}`}>
        {config.icon}
      </div>
    </div>
  );
}