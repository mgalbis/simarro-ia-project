import React from "react";

export default function MetricsCard({
    title = "INDICADORES DE CALIDAD DEL CICLO",
    modelName = "Evaluación QA",
    status = "ACTIVE",
    metrics = [],
    history = [],
    activeExecutionId = null,
    hasReport = false,
    hideTitle = false,
  }) {
  const enrichedMetrics = enrichMetrics(metrics, history, activeExecutionId);
  const hasMetrics = hasReport && Array.isArray(enrichedMetrics) && enrichedMetrics.length > 0;

  return (
    <div className="bg-black/30 border border-qa-border-glow rounded-xl p-4 shadow-[inset_0_0_15px_rgba(142,53,255,0.1)]">
      {!hideTitle && (
        <div className="flex items-center gap-2 text-qa-purple-light font-black text-[14px] tracking-wider uppercase mb-3">
          <span className="text-qa-magenta text-lg">⌁</span>
          {title}
        </div>
      )}

      <div className="flex justify-between items-center mb-5 px-1">
        <div className="text-[13px] font-extrabold text-qa-purple-light tracking-tight">
          Contexto: <span className="text-white">{modelName}</span>
        </div>

        <div className="flex items-center gap-1.5 text-[10px] font-black tracking-widest text-qa-green">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-qa-green opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-qa-green"></span>
          </span>
          {status}
        </div>
      </div>

      {!hasMetrics ? (
        <div className="px-2 py-6 text-qa-muted text-[12px] text-center italic leading-relaxed">
          Todavía no hay ciclos de pruebas guardados. Crea un nuevo ciclo o lanza una solicitud de pruebas.
        </div>
      ) : (
        <div className="space-y-4">
          {enrichedMetrics.map((m, index) => (
            <MetricRow
              key={`${m.label}-${index}`}
              label={m.label}
              value={m.value}
              previous={m.previous}
              average={m.average}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function enrichMetrics(currentMetrics, history, activeExecutionId) {
  return currentMetrics.map((metric) => {
    const previous = getPreviousMetricValue(
      metric.label,
      history,
      activeExecutionId
    );

    const average = getAverageMetricValue(metric.label, history, metric.value);

    return {
      ...metric,
      previous,
      average,
    };
  });
}

function getPreviousMetricValue(label, history, activeExecutionId) {
  if (!Array.isArray(history) || history.length < 2 || !activeExecutionId) {
    return null;
  }

  const activeIndex = history.findIndex(
    (item) =>
      item.execution_id === activeExecutionId ||
      item.id === activeExecutionId ||
      item.report?.execution_id === activeExecutionId
  );

  if (activeIndex < 0) return null;

  const previousReport = history[activeIndex + 1]?.report;

  if (!previousReport) return null;

  const previousMetric = previousReport.metrics?.find((m) => m.label === label);

  return typeof previousMetric?.value === "number" ? previousMetric.value : null;
}

function getAverageMetricValue(label, history, currentValue) {
  const values = [];

  if (Array.isArray(history)) {
    history.forEach((item) => {
      const metric = item.report?.metrics?.find((m) => m.label === label);

      if (typeof metric?.value === "number") {
        values.push(metric.value);
      }
    });
  }

  if (values.length === 0 && typeof currentValue === "number") {
    values.push(currentValue);
  }

  if (values.length === 0) return null;

  const average = values.reduce((a, b) => a + b, 0) / values.length;

  return Math.round(average);
}

function MetricRow({ label, value, previous, average }) {
  const delta =
    typeof previous === "number" && typeof value === "number"
      ? value - previous
      : null;

  const deltaLabel =
    delta === null
      ? "—"
      : delta > 0
        ? `↑ +${delta}`
        : delta < 0
          ? `↓ ${delta}`
          : "→ 0";

  const safeValue = clampPercent(typeof value === "number" ? value : 0);
  const safePrevious =
    typeof previous === "number" ? clampPercent(previous) : null;
  const safeAverage =
    typeof average === "number" ? clampPercent(average) : null;

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between text-[11px] font-bold uppercase tracking-tighter text-qa-muted">
        <span>{label}</span>
        <span className="text-white font-black">{safeValue}%</span>
      </div>

      <div className="relative flex items-center gap-3">
        <div className="relative flex-1 h-3 bg-slate-900/80 rounded-full border border-white/5 overflow-visible">
          {/* Valor actual */}
          <div
            className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-qa-purple via-qa-purple-light to-qa-magenta shadow-[0_0_10px_rgba(142,53,255,0.6)] transition-all duration-1000 ease-out"
            style={{ width: `${safeValue}%` }}
            title={`Actual: ${safeValue}%`}
          />

          {/* Marcador valor anterior */}
          {safePrevious !== null && (
            <div
              className="absolute top-[-4px] h-5 w-[2px] bg-white shadow-[0_0_6px_rgba(255,255,255,0.8)]"
              style={{ left: `${safePrevious}%` }}
              title={`Anterior: ${safePrevious}%`}
            />
          )}

          {/* Marcador media */}
          {safeAverage !== null && (
            <div
              className="absolute top-[-3px] h-4 w-[2px] bg-yellow-300 shadow-[0_0_6px_rgba(250,204,21,0.8)]"
              style={{ left: `${safeAverage}%` }}
              title={`Media: ${safeAverage}%`}
            />
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-[9px] text-qa-muted">
        <div>
          Actual: <span className="text-white font-bold">{safeValue}%</span>
        </div>

        <div>
          Anterior:{" "}
          <span className="text-white font-bold">
            {safePrevious === null ? "—" : `${safePrevious}%`}
          </span>
        </div>

        <div>
          Media:{" "}
          <span className="text-white font-bold">
            {safeAverage === null ? "—" : `${safeAverage}%`}
          </span>
        </div>
      </div>

      <div className="flex justify-between gap-2 text-[9px] text-qa-purple-light font-bold">
        <span>Variación última iteración: {deltaLabel}</span>
        <span className="text-white/40">
          marcador blanco = anterior · amarillo = media
        </span>
      </div>
    </div>
  );
}

function clampPercent(value) {
  return Math.max(0, Math.min(100, Math.round(value)));
}