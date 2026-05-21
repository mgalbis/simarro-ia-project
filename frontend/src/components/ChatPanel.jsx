import React, { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";

export default function ChatPanel({
  messages,
  input,
  setInput,
  sendMessage,
  clearChat,
  clearActiveReview,
  onFileUpload,
  selectedFile,
  isLoading,
  lastReport,
  downloadEnabled,
  activeReviewPrompt,
  pendingPrompt,
  sessionId,
  availableSessions = [],
  onUpdateCycleMetadata = null,
  inferTestPhaseFromPrompt = null,
  onReportPhaseFeedback = null,
  user = null,
  onLogout = null,
}) {
  const fileInputRef = useRef(null);

  const chatScrollRef = useRef(null);
  const chatTopRef = useRef(null);
  const chatBottomRef = useRef(null);

  const [isAtTop, setIsAtTop] = useState(true);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);
  const [projectLabel, setProjectLabel] = useState("");
  const [reviewLabel, setReviewLabel] = useState("");
  const [phaseFeedbackComment, setPhaseFeedbackComment] = useState("");
  const [showPhaseFeedback, setShowPhaseFeedback] = useState(false);
  const [isCycleConfigExpanded, setIsCycleConfigExpanded] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  
  const updateScrollPosition = () => {
    const element = chatScrollRef.current;

    if (!element) return;

    const threshold = 12;

    const atTop = element.scrollTop <= threshold;
    const atBottom =
      element.scrollHeight - element.scrollTop - element.clientHeight <= threshold;

    setIsAtTop(atTop);
    setIsAtBottom(atBottom);
  };

  useEffect(() => {
    if (autoScrollEnabled) {
      chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }

    window.setTimeout(updateScrollPosition, 80);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, autoScrollEnabled]);

  const scrollToTop = () => {
    chatTopRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const scrollToBottom = () => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];

    if (file) {
      onFileUpload(file);
    }
  };

  const handleDownload = () => {
    const executionId = lastReport?.execution_id;

    if (!executionId) {
      alert("No hay ningún informe disponible para descargar.");
      return;
    }

    window.open(`http://localhost:8000/download/${executionId}?user_id=${user?.id}`, "_blank");
  };

  const hasReport = Boolean(lastReport?.execution_id);

  const activeSession =
    availableSessions.find((session) => session.session_id === sessionId) || null;

  const activePrompt = activeReviewPrompt || pendingPrompt || input || "";

  const detectedPhase =
    activeSession?.test_phase ||
    inferTestPhaseFromPrompt?.(activePrompt) ||
    "Fase no determinada";

  const hasCycleContext = Boolean(sessionId || activeReviewPrompt || pendingPrompt);

  const isCycleConfigured = Boolean(
    activeSession?.project_label &&
    activeSession?.review_label
  );

  const [loginTime] = useState(() =>
    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  );

  useEffect(() => {
    setProjectLabel(activeSession?.project_label || "");
    setReviewLabel(activeSession?.review_label || "");

    const configured = Boolean(
      activeSession?.project_label &&
      activeSession?.review_label
    );

    setIsCycleConfigExpanded(!configured);
  }, [
    activeSession?.session_id,
    activeSession?.project_label,
    activeSession?.review_label,
  ]);

  const handleSaveCycleConfiguration = async () => {
    if (!projectLabel.trim() || !reviewLabel.trim()) {
      alert("Debes indicar proyecto y título del ciclo de pruebas.");
      return;
    }

    if (!onUpdateCycleMetadata) {
      alert("La actualización de datos del ciclo no está conectada.");
      return;
    }

    await onUpdateCycleMetadata({
      project_label: projectLabel.trim(),
      review_label: reviewLabel.trim(),
      test_phase: detectedPhase,
    });

    setIsCycleConfigExpanded(false);
  };

  const handleReportPhaseFeedback = async () => {
    if (!onReportPhaseFeedback) {
      alert("El registro de incidencias de fase no está conectado.");
      return;
    }

    await onReportPhaseFeedback({
      detected_phase: detectedPhase,
      comment: phaseFeedbackComment.trim(),
    });

    setPhaseFeedbackComment("");
    setShowPhaseFeedback(false);
  };

  return (
    <main className="flex flex-col gap-2 h-full max-h-screen overflow-hidden">
      {/* TARJETA CENTRAL */}
      <div className="relative flex-1 bg-qa-panel border-2 border-qa-purple/40 rounded-[22px] backdrop-blur-xl shadow-[0_0_30px_rgba(142,53,255,0.15)] p-4 flex flex-col overflow-hidden">
        {/* HEADER */}
        <div className="flex items-center gap-4 mb-4 border-b border-qa-purple/20 pb-4">
          <div className="w-[70px] h-[70px] rounded-3xl bg-qa-bot-gradient shadow-[0_0_20px_rgba(142,53,255,0.70)]">
            <img src="/QABotIcon.png" alt="Bot Icon" className="w-full h-full object-contain scale-105" />
          </div>

          <div className="flex-1">
            <h1 className="text-[28px] font-[900] leading-none tracking-wider text-white italic">
              QABot - Asistente de Calidad
            </h1>
            <h2 className="text-[11px] font-[800] uppercase text-qa-purple-light mt-1 tracking-widest">
              OFICINA DE TEST INTELIGENTE
            </h2>
          </div>

          {/* WIDGET DE USUARIO */}
          {user && (
            <div className="relative flex-shrink-0">
              {/* Botón principal */}
              <button
                onClick={() => setShowUserMenu((v) => !v)}
                className="flex items-center gap-2.5 bg-black/40 border border-qa-purple/30 rounded-xl px-3 py-2 hover:border-qa-purple/60 transition-all"
              >
                {/* Avatar */}
                <div className="w-8 h-8 rounded-xl bg-qa-bot-gradient shadow-[0_0_10px_rgba(142,53,255,0.5)] overflow-hidden flex-shrink-0">
                  <img src="/QABotIcon.png" alt="user" className="w-full h-full object-contain" />
                </div>

                <div className="flex flex-col items-start">
                  <span className="text-[12px] font-black text-white capitalize leading-none">
                    {user.username}
                  </span>
                  <span className="flex items-center gap-1 text-[9px] text-qa-green font-bold uppercase tracking-wider mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-qa-green shadow-[0_0_4px_rgba(0,255,133,0.8)] inline-block" />
                    Activo
                  </span>
                </div>

                {/* Chevron */}
                <span className={`text-white/40 text-xs transition-transform ${showUserMenu ? "rotate-180" : ""}`}>
                  ▼
                </span>
              </button>

              {/* Dropdown */}
              {showUserMenu && (
                <>
                  {/* Overlay para cerrar al hacer click fuera */}
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowUserMenu(false)}
                  />

                  <div className="absolute right-0 top-[calc(100%+8px)] z-20 w-[200px] bg-[#0e0e1f] border border-qa-purple/30 rounded-xl shadow-[0_0_25px_rgba(0,0,0,0.6)] overflow-hidden">
                    
                    {/* Estado activo */}
                    <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-qa-green shadow-[0_0_6px_rgba(0,255,133,0.8)]" />
                        <span className="text-[11px] text-qa-green font-bold">Estado activo</span>
                      </div>
                      <span className="text-[11px] text-white/40 font-mono">{loginTime}</span>
                    </div>

                    {/* Cerrar sesión */}
                    <button
                      onClick={() => {
                        setShowUserMenu(false);
                        onLogout?.();
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 text-[11px] font-black text-white/70 hover:bg-red-600/20 hover:text-red-400 transition-all"
                    >
                      <span className="text-base">⏻</span>
                      <span>Cerrar sesión</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* CONTENEDOR CHAT */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* MENSAJES */}
          <div
            ref={chatScrollRef}
            onScroll={updateScrollPosition}
            className="h-full overflow-y-auto p-4 pb-24 scrollbar-thin relative"
          >
            <div ref={chatTopRef} />

            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
                <div className="text-5xl mb-3">💬</div>

                <h3 className="text-lg font-bold text-white mb-1">
                  Inicia una conversación
                </h3>

                <p className="text-qa-muted text-sm">
                  Carga un archivo o haz una consulta
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                {messages.map((msg, index) => (
                  <MessageBubble
                    key={msg.id || index}
                    role={msg.role}
                    content={msg.content}
                    timestamp={msg.timestamp}
                  />
                ))}
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>

          {/* BOTONES FLOTANTES */}
          <div className="absolute bottom-3 right-8 z-10 flex gap-2">
            {!isAtTop && (
              <button
                onClick={scrollToTop}
                title="Ir al inicio del chat"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider bg-white/5 text-white/60 border border-white/10 hover:bg-qa-purple hover:text-white transition-all"
              >
                ↑ Inicio
              </button>
            )}

            {!isAtBottom && (
              <button
                onClick={scrollToBottom}
                title="Ir al final del chat"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider bg-white/5 text-white/60 border border-white/10 hover:bg-qa-purple hover:text-white transition-all"
              >
                ↓ Final
              </button>
            )}

            <button
              onClick={() => setAutoScrollEnabled((value) => !value)}
              title={
                autoScrollEnabled
                  ? "Desactivar scroll automático"
                  : "Activar scroll automático"
              }
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider border transition-all ${
                autoScrollEnabled
                  ? "bg-qa-green/10 text-qa-green border-qa-green/30 hover:bg-qa-green/20"
                  : "bg-white/5 text-white/50 border-white/10 hover:bg-qa-purple hover:text-white"
              }`}
            >
              {autoScrollEnabled ? "AUTO ↓ ON" : "AUTO ↓ OFF"}
            </button>

            <button
              onClick={handleDownload}
              disabled={!hasReport}
              title={hasReport ? "Descargar informe" : "Ejecuta un análisis primero"}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all ${
                hasReport
                  ? "bg-gradient-to-r from-[#4f46e5] to-[#7c3aed] text-white shadow-[0_0_12px_rgba(124,58,237,0.4)] hover:brightness-110 hover:scale-105 active:scale-95 cursor-pointer"
                  : "bg-white/5 text-white/25 border border-white/10 cursor-not-allowed"
              }`}
            >
              <span>DESCARGAR INFORME</span>
              <span>{hasReport ? "📥" : "🔒"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* TARJETA DE CONTROLES */}
      <div className="bg-qa-panel/80 border-2 border-qa-purple/40 rounded-2xl p-4 flex flex-col gap-4 shadow-[0_10px_40px_rgba(0,0,0,0.5)]">
        {hasCycleContext && (
          <div className="bg-black/30 border border-qa-purple/30 rounded-xl px-4 py-3 text-[11px] text-qa-muted leading-relaxed">
            <div className="flex justify-between gap-3 items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <div className="text-qa-purple-light font-black uppercase tracking-wider">
                    Configuración del ciclo de pruebas
                  </div>

                  <div
                    className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-full border ${
                      isCycleConfigured
                        ? "text-qa-green border-qa-green/30 bg-qa-green/10"
                        : "text-yellow-300 border-yellow-300/30 bg-yellow-300/10"
                    }`}
                  >
                    {isCycleConfigured ? "Configurado" : "Pendiente"}
                  </div>
                </div>

                {isCycleConfigured && !isCycleConfigExpanded ? (
                  <div className="mt-2 flex items-center gap-2 text-[10px] min-w-0">
                    <span className="text-white/40 uppercase font-black shrink-0">
                      Proyecto:
                    </span>
                    <span className="text-white font-bold truncate">
                      {activeSession?.project_label}
                    </span>

                    <span className="text-white/25 shrink-0">·</span>

                    <span className="text-white/40 uppercase font-black shrink-0">
                      Ciclo:
                    </span>
                    <span className="text-white font-bold truncate">
                      {activeSession?.review_label}
                    </span>

                    <span className="text-white/25 shrink-0">·</span>

                    <span className="text-white/40 uppercase font-black shrink-0">
                      Fase:
                    </span>
                    <span className="text-white font-bold truncate">
                      {activeSession?.test_phase || detectedPhase}
                    </span>
                  </div>
                ) : (
                  <div className="mt-2 text-white/50">
                    Completa los datos obligatorios antes de ejecutar la primera iteración.
                  </div>
                )}
              </div>

              {isCycleConfigured && (
                <button
                  type="button"
                  className="text-[10px] uppercase font-black text-white/70 border border-white/10 rounded-lg px-3 py-2 hover:bg-qa-purple hover:text-white transition-all"
                  onClick={() => setIsCycleConfigExpanded((value) => !value)}
                >
                  {isCycleConfigExpanded ? "Ocultar" : "Editar"}
                </button>
              )}
            </div>

            {(!isCycleConfigured || isCycleConfigExpanded) && (
              <>
                <div className="grid grid-cols-3 gap-3 mt-3">
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] text-white/50 uppercase font-bold">
                      Proyecto *
                    </label>
                    <input
                      className="bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-[11px] outline-none focus:border-qa-purple"
                      placeholder="Ej. Demo QABot"
                      value={projectLabel}
                      onChange={(event) => setProjectLabel(event.target.value)}
                      maxLength={25}
                    />
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] text-white/50 uppercase font-bold">
                      Título del ciclo *
                    </label>
                    <input
                      className="bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-[11px] outline-none focus:border-qa-purple"
                      placeholder="Ej. Validación calidad dataset abandono"
                      value={reviewLabel}
                      onChange={(event) => setReviewLabel(event.target.value)}
                      maxLength={40}
                    />
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] text-white/50 uppercase font-bold">
                      Fase detectada
                    </label>
                    <input
                      className="bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white/70 text-[11px] outline-none cursor-not-allowed"
                      value={detectedPhase}
                      readOnly
                    />
                  </div>
                </div>

                <div className="flex justify-between gap-3 items-center mt-3">
                  <button
                    type="button"
                    className="text-[10px] uppercase font-black text-white/60 hover:text-qa-purple-light transition-all"
                    onClick={() => setShowPhaseFeedback((value) => !value)}
                  >
                    {showPhaseFeedback
                      ? "Ocultar incidencia de fase"
                      : "Reportar fase incorrecta"}
                  </button>

                  <button
                    type="button"
                    className="text-[10px] uppercase font-black text-white/80 border border-white/10 rounded-lg px-3 py-2 hover:bg-qa-purple hover:text-white transition-all"
                    onClick={handleSaveCycleConfiguration}
                  >
                    Guardar configuración
                  </button>
                </div>

                {showPhaseFeedback && (
                  <div className="mt-3 flex flex-col gap-2">
                    <textarea
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-[11px] outline-none focus:border-qa-purple min-h-[70px]"
                      placeholder="Describe por qué la fase detectada no es correcta..."
                      value={phaseFeedbackComment}
                      onChange={(event) => setPhaseFeedbackComment(event.target.value)}
                    />

                    <button
                      type="button"
                      className="self-end text-[10px] uppercase font-black text-white/80 border border-white/10 rounded-lg px-3 py-2 hover:bg-qa-purple hover:text-white transition-all"
                      onClick={handleReportPhaseFeedback}
                    >
                      Registrar incidencia
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}
        {/* CICLO DE PRUEBAS ACTIVO */}
        {(activeReviewPrompt || pendingPrompt) && (
          <div className="bg-black/30 border border-qa-purple/30 rounded-xl px-4 py-3 text-[11px] text-qa-muted leading-relaxed">
            <div className="flex justify-between gap-3 items-center">
              <div className="flex-1">
                <div className="text-qa-purple-light font-black uppercase tracking-wider mb-1">
                  Ciclo de pruebas activo
                </div>

                <div className="italic line-clamp-2">
                  {activeReviewPrompt || pendingPrompt}
                </div>

                {pendingPrompt && (
                  <div className="text-yellow-300 mt-1 font-bold">
                    Pendiente de dataset. Se ejecutará automáticamente al subir el artefacto.
                  </div>
                )}
              </div>

              {clearActiveReview && (
                <button
                  className="text-[10px] uppercase font-black text-white/70 border border-white/10 rounded-lg px-2 py-1 hover:bg-red-600 hover:text-white transition-all"
                  onClick={clearActiveReview}
                  title="Limpiar ciclo de pruebas activo"
                >
                  Cambiar ciclo de pruebas
                </button>
              )}
            </div>
          </div>
        )}

        {/* FILA DE ARCHIVO */}
        <div className="flex gap-3 items-center">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept=".csv"
          />

          <button
            className="flex items-center gap-2 bg-[#1a1a2e] border border-qa-purple/50 px-4 py-2.5 rounded-xl text-[11px] font-black text-qa-purple-light shadow-[0_0_15px_rgba(142,53,255,0.1)] hover:bg-qa-purple hover:text-white transition-all uppercase whitespace-nowrap"
            onClick={() => fileInputRef.current.click()}
          >
            <span>UPLOAD</span>
            <span className="text-sm">📤</span>
          </button>

          <div className="flex-1 bg-black/40 border border-qa-purple/20 rounded-xl px-4 py-2.5 flex items-center">
            <span className="text-[11px] text-qa-muted italic truncate">
              {selectedFile ? `📄 ${selectedFile.name}` : "No hay archivo seleccionado..."}
            </span>
          </div>
        </div>

        {/* INPUT MENSAJE */}
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              className="w-full bg-[#050509] border-2 border-qa-purple/20 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-qa-purple/60 transition-all placeholder:text-gray-500 shadow-inner"
              placeholder="Escribir mensaje..."
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !isLoading) {
                  sendMessage();
                }
              }}
            />
          </div>

          <button
            className="bg-gradient-to-r from-qa-purple to-[#5b13db] px-5 py-2 rounded-xl text-[11px] font-black text-white shadow-[0_0_15px_rgba(142,53,255,0.4)] hover:brightness-110 hover:scale-105 active:scale-95 transition-all uppercase disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={sendMessage}
            disabled={isLoading}
          >
            {isLoading ? "Ejecutando..." : "➤ Enviar"}
          </button>

          <button
            className="bg-gradient-to-r from-[#2e1065] to-[#1e1b4b] border border-white/10 px-6 py-2 rounded-xl text-[11px] font-black text-white/70 hover:from-red-600 hover:to-red-800 hover:text-white hover:border-red-500 hover:shadow-[0_0_20px_rgba(239,68,68,0.4)] active:scale-95 transition-all duration-300 uppercase"
            onClick={clearChat}
          >
            Limpiar
          </button>
        </div>
      </div>
    </main>
  );
}