import React, { useState } from "react";

export default function LeftPanel({
  onNewSession,
  sessions = [],
  sessionId = null,
  onRestoreSession = null,
  onUpdateCycleMetadata = null,
  isCollapsed = false,
  onToggleCollapse = null,
  searchText,
  setSearchText,
  projectFilter,
  setProjectFilter,
  phaseFilter,
  setPhaseFilter,
}) {
  const [sessionToRestore, setSessionToRestore] = useState("");

  const activeSession = sessions.find(
    (session) => session.session_id === sessionId
  );

  const projects = Array.from(
    new Set(sessions.map((s) => s.project_label).filter(Boolean))
  );

  const phases = Array.from(
    new Set(sessions.map((s) => s.test_phase).filter(Boolean))
  );

  const filteredSessions = sessions.filter((session) => {
    const matchesProject =
      projectFilter === "ALL" || session.project_label === projectFilter;

    const matchesPhase =
      phaseFilter === "ALL" || session.test_phase === phaseFilter;

    const query = searchText.trim().toLowerCase();

    const matchesSearch =
      !query ||
      [
        session.title,
        session.review_label,
        session.project_label,
        session.test_phase,
        session.active_review_prompt,
        session.session_id,
      ]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(query));

    return matchesProject && matchesPhase && matchesSearch;
  });

  const getStatusClass = (status) => {
    switch (status?.toUpperCase()) {
      case "PASS":
      case "SUCCESS":
        return "text-qa-green";
      case "WARN":
      case "WARNING":
        return "text-yellow-400";
      case "FAIL":
      case "ERROR":
        return "text-qa-magenta";
      default:
        return "text-white/50";
    }
  };

  if (isCollapsed) {
    return (
      <aside className="bg-qa-panel border border-qa-border rounded-[22px] backdrop-blur-xl shadow-[0_0_25px_rgba(142,53,255,0.25)] p-3 flex flex-col items-center h-full overflow-hidden">
        <button
          className="w-10 h-10 rounded-xl bg-black/30 border border-qa-purple/40 text-white hover:bg-qa-purple transition-all"
          onClick={onToggleCollapse}
          title="Expandir panel de ciclos"
        >
          →
        </button>

        <button
          className="mt-auto w-10 h-10 rounded-xl bg-gradient-to-r from-qa-purple to-[#4300a3] text-white font-black hover:scale-105 active:scale-95 transition-all"
          onClick={() => onNewSession?.()}
          title="Nuevo ciclo de pruebas"
        >
          ＋
        </button>
      </aside>
    );
  }

  return (
    <aside className="bg-qa-panel border border-qa-border rounded-[22px] backdrop-blur-xl shadow-[0_0_25px_rgba(142,53,255,0.25)] p-4 flex flex-col gap-5 h-full overflow-y-auto">
      {/* CABECERA */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-qa-purple-light font-[900] text-[12px] tracking-[0.15em] uppercase">
          <div className="w-5 h-5 border border-qa-purple-light rounded-full flex items-center justify-center text-[10px] font-bold">
            C
          </div>
          CICLOS DE PRUEBAS
        </div>

        <button
          className="flex items-center gap-1 px-2 py-1 rounded-lg bg-black/30 border border-white/10 text-white/70 hover:bg-qa-purple hover:text-white transition-all text-[10px] font-black uppercase"
          onClick={onToggleCollapse}
          title="Colapsar panel de ciclos de pruebas"
        >
          <span>←</span>
          <span>Colapsar</span>
        </button>
      </div>

      {/* LISTA DE CICLOS */}
      <div className="bg-[#0c0d21]/50 border border-qa-border-glow rounded-[20px] p-4 flex flex-col gap-3">
        <div className="flex justify-between items-center">
          <div className="text-[11px] text-qa-purple-light font-black uppercase tracking-wider">
            Ciclos de pruebas disponibles
          </div>

          <span className="text-[10px] text-white/50">
            {sessions.length}
          </span>
        </div>

        <div className="flex flex-col gap-2">
          <input
            className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-[11px] outline-none focus:border-qa-purple"
            placeholder="Filtrar por proyecto, fase o ciclo de pruebas..."
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
          />

          <div className="grid grid-cols-2 gap-2">
            <select
              className="bg-black/40 border border-white/10 rounded-lg px-2 py-2 text-white text-[10px] outline-none focus:border-qa-purple"
              value={projectFilter}
              onChange={(event) => setProjectFilter(event.target.value)}
            >
              <option value="ALL">Todos los proyectos</option>
              {projects.map((project) => (
                <option key={project} value={project}>
                  {project}
                </option>
              ))}
            </select>

            <select
              className="bg-black/40 border border-white/10 rounded-lg px-2 py-2 text-white text-[10px] outline-none focus:border-qa-purple"
              value={phaseFilter}
              onChange={(event) => setPhaseFilter(event.target.value)}
            >
              <option value="ALL">Todas las fases</option>
              {phases.map((phase) => (
                <option key={phase} value={phase}>
                  {phase}
                </option>
              ))}
            </select>
          </div>
        </div>

        {sessions.length === 0 ? (
          <div className="text-[11px] text-qa-muted italic leading-relaxed">
            Todavía no hay ciclos de pruebas guardados. Crea un nuevo ciclo o lanza una solicitud de pruebas.
          </div>
        ) : (
          <div className="flex flex-col gap-2 max-h-[230px] overflow-y-auto pr-1">
            {filteredSessions.map((session) => (
              <button
                key={session.session_id}
                type="button"
                className={`text-left bg-black/30 border rounded-xl px-3 py-2 hover:border-qa-purple hover:bg-qa-purple/10 transition-all ${
                  session.session_id === sessionId
                    ? "border-qa-purple text-white"
                    : "border-white/10 text-qa-muted"
                }`}
                onClick={() => onRestoreSession && onRestoreSession(session.session_id)}
              >
                <div className="flex justify-between gap-2 items-start">
                  <span className="font-black text-[10px] uppercase leading-snug line-clamp-2">
                    {session.title || session.session_id}
                  </span>

                  <span className={`text-[9px] font-black whitespace-nowrap ${getStatusClass(session.last_status)}`}>
                    {session.last_status || "SIN EJEC."}
                  </span>
                </div>

                <div className="text-[10px] text-white/50 mt-1">
                  {session.iteration_count || 0} iteraciones
                </div>

                <div className="text-[9px] text-white/35 mt-0.5 truncate">
                  {session.updated_at || ""}
                </div>
              </button>
            ))}
          </div>
        )}

        <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-qa-purple/30 to-transparent" />

        {/* RECUPERACIÓN POR ID */}
        <div className="flex flex-col gap-2">
          <input
            className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-[11px] outline-none focus:border-qa-purple"
            placeholder="O introduce un ID técnico del ciclo"
            value={sessionToRestore}
            onChange={(e) => setSessionToRestore(e.target.value)}
          />

          <button
            type="button"
            className="w-full text-[10px] uppercase font-black text-white/80 border border-white/10 rounded-lg px-3 py-2 hover:bg-qa-purple hover:text-white transition-all"
            onClick={() => {
              if (!onRestoreSession) {
                alert("La recuperación de ciclo no está conectada.");
                return;
              }

              onRestoreSession(sessionToRestore.trim());
            }}
          >
            Recuperar ciclo
          </button>
        </div>
      </div>

      {/* LIMITACIONES */}
      <div className="flex items-center gap-2 text-qa-purple-light font-[900] text-[12px] tracking-[0.15em] uppercase">
        <div className="w-5 h-5 border border-qa-purple-light rounded-full flex items-center justify-center text-[10px] font-bold">
          i
        </div>
        LIMITACIONES
      </div>

      <div className="bg-[#0c0d21]/50 border border-qa-border-glow rounded-[20px] p-4 flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="w-[40px] h-[40px] rounded-3xl bg-qa-bot-gradient shadow-[0_0_20px_rgba(142,53,255,0.70)]">
            <img
              src="/QABotIcon.png"
              alt="Bot Icon"
              className="w-full h-full object-contain scale-105"
            />
          </div>

          <div className="leading-tight">
            <span className="text-[13px] font-black text-white block uppercase tracking-tight">
              QABot en fase
            </span>
            <span className="text-[13px] font-black text-white block uppercase tracking-tight">
              de mejora
            </span>
          </div>
        </div>

        <p className="text-[11.5px] text-qa-muted leading-relaxed font-medium">
          Soy QABot, un asistente orientado a asegurar la calidad de los artefactos generados en las distintas fases del ciclo del dato en proyectos de IA y Big Data mediante la ejecución de ciclos de pruebas.
        </p>

        <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-qa-purple/30 to-transparent" />

        <ul className="flex flex-col gap-3">
          {[
            "No corrijo artefactos: identifico defectos y evidencias.",
            "Puedo cometer errores en la interpretación.",
            "La ejecución de las pruebas depende de los artefactos aportados.",
            "Las conclusiones deben validarse dentro del ciclo de pruebas.",
          ].map((text, index) => (
            <li key={index} className="flex gap-2 items-start">
              <span className="text-qa-magenta text-[14px] leading-[14px] mt-0.5">
                ●
              </span>
              <span className="text-[11px] text-[#f3f1ff] leading-snug">
                {text}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* NUEVO CICLO DE PRUEBAS */}
      <div className="mt-auto pt-4 border-t border-qa-border/20">
        <div className="text-qa-purple-light font-black text-[11px] tracking-widest uppercase mb-3 text-center">
          NUEVO CICLO DE PRUEBAS
        </div>

        <button
          className="w-full bg-gradient-to-r from-qa-purple to-[#4300a3] py-3 rounded-xl font-[900] text-[12px] text-white shadow-[0_0_18px_rgba(142,53,255,0.3)] hover:scale-[1.02] active:scale-95 transition-all uppercase tracking-wider"
          onClick={() => onNewSession?.()}
        >
          ＋ Nuevo ciclo
        </button>
      </div>
    </aside>
  );
}