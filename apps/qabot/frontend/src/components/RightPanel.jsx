import React, { useState } from "react";
import HistoryCard from "./HistoryCard.jsx";
import MetricsCard from "./MetricsCard.jsx";

const TEST_LABELS = {
  nulls: "Nulos",
  duplicates: "Duplicados",
  data_types: "Tipos de dato",
  outliers: "Outliers",
  balance: "Balanceo",
  model_performance: "Evaluación de modelo",
  dataset_split: "Validación de particiones",
};

export default function RightPanel({
  history = [],
  lastReport = null,
  onOpenHistoricalReport = null,
  isCollapsed = false,
  onDeleteIteration = null,
  onToggleCollapse = null,
  session = null,
  user = null,
}) {
  const [collapsedSections, setCollapsedSections] = useState({
    iterations: false,
    execution: false,
    metrics: false,
  });

  const toggleSection = (sectionName) => {
    setCollapsedSections((prev) => ({
      ...prev,
      [sectionName]: !prev[sectionName],
    }));
  };

  const expandAllSections = () => {
    setCollapsedSections({
      iterations: false,
      execution: false,
      metrics: false,
    });
  };

  const collapseAllSections = () => {
    setCollapsedSections({
      iterations: true,
      execution: true,
      metrics: true,
    });
  };

  const shouldGrowSection = (sectionName) => {
    return !collapsedSections[sectionName];
  };

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

  const getActiveIterationNumber = () => {
    if (!lastReport?.execution_id) return null;

    const found = history.find(
      (item) =>
        item.execution_id === lastReport.execution_id ||
        item.id === lastReport.execution_id ||
        item.report?.execution_id === lastReport.execution_id
    );

    return found?.iterationNumber ?? null;
  };

  const getPreviousStatusForTest = (testName) => {
    if (!lastReport?.execution_id || !Array.isArray(history)) return null;

    const activeIndex = history.findIndex(
      (item) =>
        item.execution_id === lastReport.execution_id ||
        item.id === lastReport.execution_id ||
        item.report?.execution_id === lastReport.execution_id
    );

    if (activeIndex < 0) return null;

    const previousReport = history[activeIndex + 1]?.report;
    if (!previousReport?.results) return null;

    const previousResult = previousReport.results.find(
      (result) => result.name === testName
    );

    return previousResult?.status ?? null;
  };

  const getMostFrequentStatusForTest = (testName) => {
    if (!Array.isArray(history) || history.length === 0) return null;

    const counts = {};

    history.forEach((item) => {
      const result = item.report?.results?.find((r) => r.name === testName);
      const status = result?.status;

      if (!status) return;

      counts[status] = (counts[status] || 0) + 1;
    });

    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);

    return sorted[0]?.[0] ?? null;
  };

  const activeIterationNumber = getActiveIterationNumber();

  if (isCollapsed) {
    return (
      <aside className="bg-qa-panel border border-qa-border rounded-[22px] backdrop-blur-xl shadow-[0_0_25px_rgba(142,53,255,0.25)] p-3 flex flex-col items-center h-full overflow-hidden">
        <button
          className="w-10 h-10 rounded-xl bg-black/30 border border-qa-purple/40 text-white hover:bg-qa-purple transition-all"
          onClick={onToggleCollapse}
          title="Expandir panel de resultados"
        >
          ←
        </button>


      </aside>
    );
  }

  return (
    <aside className="bg-qa-panel border border-qa-border rounded-[22px] backdrop-blur-xl shadow-[0_0_25px_rgba(142,53,255,0.25)] p-4 flex flex-col gap-4 h-full overflow-hidden">
      {/* CABECERA DEL PANEL */}
      <div className="shrink-0">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-qa-purple-light font-[900] text-[12px] tracking-[0.15em] uppercase min-w-0">
            <div className="w-5 h-5 border border-qa-purple-light rounded-full flex items-center justify-center text-[10px] font-bold shrink-0">
              R
            </div>
            <span className="truncate">Panel de resultados</span>
          </div>

          <button
            className="flex items-center gap-1 px-2 py-1 rounded-lg bg-black/30 border border-white/10 text-white/70 hover:bg-qa-purple hover:text-white transition-all text-[10px] font-black uppercase shrink-0"
            onClick={onToggleCollapse}
            title="Colapsar panel de resultados"
          >
            <span>Colapsar</span>
            <span>→</span>
          </button>
        </div>

        <div className="flex gap-3 mt-3 text-[9px] uppercase font-black">
          <button
            className="text-white/45 hover:text-qa-purple-light transition-all"
            onClick={expandAllSections}
          >
            Expandir todo
          </button>

          <button
            className="text-white/45 hover:text-qa-purple-light transition-all"
            onClick={collapseAllSections}
          >
            Colapsar todo
          </button>
        </div>
      </div>

      {/* SECCIÓN 1: ITERACIONES */}
      <CollapsibleSection
        title="Iteraciones del ciclo de pruebas"
        icon="■"
        collapsed={collapsedSections.iterations}
        onToggle={() => toggleSection("iterations")}
        summary={
          history.length > 0 ? `${history.length} iteraciones` : "Sin iteraciones"
        }
        grow={shouldGrowSection("iterations")}
      >
        <div className="h-full overflow-y-auto custom-scrollbar pr-1">
          <HistoryCard
            history={history}
            session={session}
            onOpenHistoricalReport={onOpenHistoricalReport}
            hideTitle={true}
            onDeleteIteration={onDeleteIteration}
            user={user}
          />
        </div>
      </CollapsibleSection>

      {/* SECCIÓN 2: RESULTADO DE EJECUCIÓN / ITERACIÓN */}
      <CollapsibleSection
        title={
          activeIterationNumber
            ? `Iteración ${activeIterationNumber}`
            : "Última ejecución"
        }
        icon="▣"
        collapsed={collapsedSections.execution}
        onToggle={() => toggleSection("execution")}
        summary={
          lastReport?.global_status
            ? `Global: ${lastReport.global_status}`
            : "Sin resultados"
        }
        grow={shouldGrowSection("execution")}
      >
        <div className="h-full overflow-y-auto custom-scrollbar pr-1">
          {!lastReport ? (
            <p className="text-[11px] text-qa-muted italic leading-relaxed">
              Todavía no hay resultados. Carga un CSV y solicita una validación
              para ver el reporte.
            </p>
          ) : (
            <div className="space-y-3">
              <div className="flex justify-between items-end border-b border-qa-border/30 pb-2">
                <div className="text-[10px] text-qa-muted uppercase font-bold tracking-tighter">
                  ID: {lastReport.execution_id || "N/A"}
                </div>

                <div className="text-[12px] font-bold text-white text-right">
                  Global:{" "}
                  <span className={getStatusClass(lastReport.global_status)}>
                    {lastReport.global_status}
                  </span>

                  {activeIterationNumber && (
                    <div className="text-[9px] text-white/40 font-bold mt-0.5">
                      Iteración {activeIterationNumber}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-2">
                {lastReport.results?.map((r, i) => {
                  const previousStatus =
                    r.previous_status || getPreviousStatusForTest(r.name);

                  const frequentStatus =
                    r.most_frequent_status || getMostFrequentStatusForTest(r.name);

                  return (
                    <div
                      key={`${r.name}-${i}`}
                      className="flex justify-between items-center text-[10px] bg-black/30 p-2 rounded-lg border border-white/5 hover:border-qa-purple/30 transition-colors"
                    >
                      <div className="flex flex-col min-w-0">
                        <span className="text-white/90 font-bold truncate">
                          {TEST_LABELS[r.name] ?? r.name}
                        </span>

                        <span className="text-[9px] text-qa-muted">
                          Ant:{" "}
                          <span className={getStatusClass(previousStatus)}>
                            {previousStatus || "—"}
                          </span>
                          {" · "}
                          Frec:{" "}
                          <span className={getStatusClass(frequentStatus)}>
                            {frequentStatus || "—"}
                          </span>
                        </span>

                        {r.details && (
                          <span className="text-[9px] text-qa-muted truncate">
                            {r.details}
                          </span>
                        )}
                      </div>

                      <span className={getStatusClass(r.status)}>
                        {r.status}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </CollapsibleSection>

      {/* SECCIÓN 3: INDICADORES */}
      <CollapsibleSection
        title="Indicadores de calidad del ciclo"
        icon="⌁"
        collapsed={collapsedSections.metrics}
        onToggle={() => toggleSection("metrics")}
        summary={
          lastReport?.metrics?.length
            ? `${lastReport.metrics.length} indicadores`
            : "Sin indicadores"
        }
        grow={shouldGrowSection("metrics")}
      >
        <div className="h-full overflow-y-auto custom-scrollbar pr-1">
          <MetricsCard
            title=""
            modelName={
              activeIterationNumber
                ? `Iteración ${activeIterationNumber}`
                : lastReport
                  ? "Ciclo de pruebas"
                  : "Sin actividad"
            }
            status={lastReport ? "COMPLETED" : "WAITING"}
            metrics={lastReport?.metrics ?? []}
            history={history}
            activeExecutionId={lastReport?.execution_id}
            hasReport={Boolean(lastReport)}
            hideTitle={true}
          />
        </div>
      </CollapsibleSection>

      {/* LOGO */}
      <div className="mt-auto pt-4 flex justify-center border-t border-qa-border/20 shrink-0">
        <img
          src="/QABotSimarro.png"
          alt="IES Lluis Simarro"
          className="w-[200px] md:w-[240px] opacity-90 filter grayscale brightness-125 contrast-110 drop-shadow-[0_0_12px_rgba(142,53,255,0.5)]"
        />
      </div>
    </aside>
  );
}

function CollapsibleSection({
  title,
  icon = "▣",
  collapsed = false,
  onToggle,
  summary = null,
  children,
  grow = false,
}) {
  return (
    <div
      className={`bg-[#0c0d21]/40 border border-qa-border-glow rounded-xl overflow-hidden flex flex-col ${
        collapsed ? "shrink-0" : grow ? "flex-1 min-h-0" : "shrink-0"
      }`}
    >
      <div className="flex items-center justify-between gap-3 px-4 py-3 shrink-0">
        <div className="flex items-center gap-2 text-qa-purple-light font-black text-[13px] tracking-wider uppercase min-w-0">
          <span className="text-qa-magenta text-lg shrink-0">{icon}</span>
          <span className="truncate">{title}</span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {summary && (
            <div className="text-[10px] text-white/45 font-bold truncate max-w-[120px]">
              {summary}
            </div>
          )}

          <button
            type="button"
            className="w-7 h-7 rounded-lg bg-black/30 border border-white/10 text-white/70 hover:bg-qa-purple hover:text-white transition-all text-[12px] font-black"
            onClick={onToggle}
            title={collapsed ? "Mostrar sección" : "Ocultar sección"}
          >
            {collapsed ? "+" : "−"}
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className="px-4 pb-4 min-h-0 flex-1 overflow-hidden">
          {children}
        </div>
      )}
    </div>
  );
}