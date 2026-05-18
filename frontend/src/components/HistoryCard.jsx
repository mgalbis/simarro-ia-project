import React from "react";

export default function HistoryCard({
  history = [],
  onOpenHistoricalReport,
  onDownloadArtifacts,
  hideTitle = false,
}) {
  const getStatusClass = (status) => {
    switch (status?.toUpperCase()) {
      case "SUCCESS":
      case "PASS":
        return "text-qa-green border-qa-green/40 bg-qa-green/10";
      case "WARN":
      case "WARNING":
        return "text-yellow-300 border-yellow-300/40 bg-yellow-300/10";
      case "FAIL":
      case "ERROR":
        return "text-qa-magenta border-qa-magenta/40 bg-qa-magenta/10";
      default:
        return "text-qa-muted border-white/10 bg-white/5";
    }
  };

  const getStatusLabel = (status) => {
    switch (status?.toUpperCase()) {
      case "SUCCESS":
      case "PASS":
        return "CORRECTA";
      case "WARN":
      case "WARNING":
        return "AVISO";
      case "FAIL":
      case "ERROR":
        return "FALLIDA";
      default:
        return "SIN EJEC.";
    }
  };

  const handleOpenPdf = (event, executionId) => {
    event.stopPropagation();

    if (!executionId) {
      alert("No hay informe PDF disponible para esta iteración.");
      return;
    }

    window.open(`http://localhost:8000/download/${executionId}`, "_blank");
  };

  const handleDownloadArtifacts = (event, item) => {
    event.stopPropagation();

    if (onDownloadArtifacts) {
      onDownloadArtifacts(item);
      return;
    }

    const sessionId = item.session_id || item.report?.session_id;
    const executionId = item.execution_id || item.id || item.report?.execution_id;

    if (!sessionId || !executionId) {
      alert("No se han encontrado los identificadores necesarios para descargar los artefactos.");
      return;
    }

    window.open(
      `http://localhost:8000/download/artifacts/${sessionId}/${executionId}`,
      "_blank"
    );
  };

  return (
    <div className="flex flex-col gap-3 h-full">
      {!hideTitle && (
        <div className="flex items-center gap-2 text-qa-purple-light font-black text-[13px] tracking-wider uppercase">
          <span className="text-qa-magenta text-lg">■</span>
          Iteraciones del ciclo de pruebas
        </div>
      )}

      {history.length === 0 ? (
        <div className="h-full min-h-[110px] flex items-center justify-center text-center">
          <p className="text-[11px] text-qa-muted italic leading-relaxed">
            Todavía no hay iteraciones en este ciclo de pruebas.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {history.map((item, index) => {
            const executionId =
              item.execution_id || item.id || item.report?.execution_id;

            const iterationNumber =
              item.iterationNumber ?? history.length - index;

            const status = item.status || item.report?.global_status;
            const statusLabel = getStatusLabel(status);

            const fileName =
              item.fileName ||
              item.file_name ||
              item.report?.quality_assessment_order?.artifacts?.dataset?.name ||
              "Dataset recuperado";

            const date = item.date || "Histórico";
            const time = item.time || executionId || "";

            return (
              <div
                key={executionId || index}
                role="button"
                tabIndex={0}
                onClick={() => onOpenHistoricalReport?.(item.report || item)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    onOpenHistoricalReport?.(item.report || item);
                  }
                }}
                className="group bg-black/30 border border-white/5 hover:border-qa-purple/50 hover:bg-qa-purple/10 rounded-xl p-3 cursor-pointer transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 shrink-0 rounded-xl border border-qa-purple/60 bg-black/40 flex items-center justify-center text-qa-purple-light font-black text-[16px] shadow-[0_0_12px_rgba(142,53,255,0.25)]">
                    {iterationNumber}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="text-white font-black text-[11px] uppercase leading-tight truncate">
                          Iteración {iterationNumber}
                        </div>

                        <div className="text-[9px] text-white/50 mt-0.5 leading-tight">
                          {date}
                          {time ? ` · ${time}` : ""}
                        </div>
                      </div>

                      <span
                        className={`shrink-0 text-[8px] font-black uppercase border rounded-full px-2 py-0.5 ${getStatusClass(
                          status
                        )}`}
                      >
                        {statusLabel}
                      </span>
                    </div>

                    <div className="text-[9px] text-white/45 mt-1 truncate">
                      {executionId || "Sin ID de ejecución"}
                    </div>

                    <div className="text-[9px] text-white/35 mt-0.5 truncate">
                      {fileName}
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-2 mt-3">
                  <button
                    type="button"
                    className="text-[8px] uppercase font-black text-white/60 border border-white/10 rounded-lg px-2 py-1 hover:bg-qa-purple hover:text-white transition-all"
                    onClick={(event) => handleDownloadArtifacts(event, item)}
                    title="Descargar artefactos utilizados en esta iteración"
                  >
                    ZIP
                  </button>

                  <button
                    type="button"
                    className="text-[8px] uppercase font-black text-white/60 border border-white/10 rounded-lg px-2 py-1 hover:bg-qa-purple hover:text-white transition-all"
                    onClick={(event) => handleOpenPdf(event, executionId)}
                    title="Descargar informe PDF de esta iteración"
                  >
                    PDF
                  </button>

                  <button
                    type="button"
                    className="text-[14px] leading-none text-qa-magenta hover:text-white transition-all px-1"
                    onClick={(event) => {
                      event.stopPropagation();
                      alert("La eliminación de iteraciones todavía no está implementada.");
                    }}
                    title="Eliminar iteración"
                  >
                    ×
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}