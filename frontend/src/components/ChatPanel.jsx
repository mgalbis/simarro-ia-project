import React, { useRef } from "react";
import MessageBubble from "./MessageBubble";

export default function ChatPanel({
  messages,
  input,
  setInput,
  sendMessage,
  clearChat,
  onFileUpload,
  selectedFile,
  isLoading,
  lastReport,
  downloadEnabled
}) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) onFileUpload(file);
  };

  const handleDownload = () => {
    if (!lastReport?.execution_id) return;
    window.open(`http://localhost:8000/download/${lastReport.execution_id}`, "_blank");
  };

  const hasReport = downloadEnabled;

  return (
    <main className="flex flex-col gap-2 h-full max-h-screen overflow-hidden">

      {/* TARJETA CENTRAL */}
      <div className="flex-1 bg-qa-panel border-2 border-qa-purple/40 rounded-[22px] backdrop-blur-xl shadow-[0_0_30px_rgba(142,53,255,0.15)] p-4 flex flex-col overflow-hidden">

        {/* HEADER */}
        <div className="flex items-center gap-4 mb-4 border-b border-qa-purple/20 pb-4">
          <div className="w-[70px] h-[70px] rounded-3xl bg-qa-bot-gradient shadow-[0_0_20px_rgba(142,53,255,0.70)]">
            <img src="/QABotIcon.png" alt="Bot Icon" className="w-full h-full object-contain scale-105" />
          </div>
          <div className="flex-1">
            <h1 className="text-[28px] font-[900] leading-none tracking-wider text-white italic">
              QABot Asistente Agéntico de Calidad
            </h1>
            <h2 className="text-[11px] font-[800] uppercase text-qa-purple-light mt-1 tracking-widest">
              OFICINA INTELIGENTE DE CALIDAD
            </h2>
          </div>
        </div>

        {/* CONTENEDOR CHAT */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* MENSAJES */}
          <div className="h-full overflow-y-auto p-4 pb-24 scrollbar-thin">
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
                    key={index}
                    role={msg.role}
                    content={msg.content}
                    timestamp={msg.timestamp}
                  />
                ))}
              </div>
            )}
          </div>
          {/* BOTÓN FIJO */}
          <div className="absolute bottom-3 right-8 z-10">
            <button
              onClick={handleDownload}
              disabled={!hasReport}
              title={hasReport ? "Descargar informe" : "Ejecuta un análisis primero"}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all
              ${
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

        {/* Fila de Archivo */}
        <div className="flex gap-3 items-center">
          <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept=".csv" />
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

        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              className="w-full bg-[#050509] border-2 border-qa-purple/20 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-qa-purple/60 transition-all placeholder:text-gray-500 shadow-inner"
              placeholder="Escribir mensaje..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
          </div>
          <button
            className="bg-gradient-to-r from-qa-purple to-[#5b13db] px-5 py-2 rounded-xl text-[11px] font-black text-white shadow-[0_0_15px_rgba(142,53,255,0.4)] hover:brightness-110 hover:scale-105 active:scale-95 transition-all uppercase"
            onClick={sendMessage}
          >
            ➤ Enviar
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