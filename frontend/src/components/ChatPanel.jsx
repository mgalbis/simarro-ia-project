import React, { useRef } from "react";
import MessageBubble from "./MessageBubble";

export default function ChatPanel({
  messages,
  input,
  setInput,
  sendMessage,
  clearChat,
  onFileUpload,
  selectedFile 
}) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      onFileUpload(file);
    }
  };

  return (
    <main className="flex flex-col gap-2 h-full max-h-screen overflow-hidden">
      
      {/* TARJETA CENTRAL */}
      <div className="flex-1 bg-qa-panel border-2 border-qa-purple/40 rounded-[22px] backdrop-blur-xl shadow-[0_0_30px_rgba(142,53,255,0.15)] p-4 flex flex-col overflow-hidden">
        
        {/* HEADER */}
        <div className="grid grid-cols-[64px_1fr_150px] gap-4 items-center mb-4">
          <div className="w-[54px] h-[54px] rounded-2xl bg-qa-bot-gradient flex items-center justify-center text-3xl shadow-[0_0_22px_rgba(142,53,255,0.55)]">
            🤖
          </div>

          <div>
            <h1 className="text-[31px] font-[900] leading-[0.92] tracking-wider text-white">QABOT</h1>
            <h2 className="text-[12.5px] font-[800] uppercase text-white mt-1">Asistente Agéntico de Calidad</h2>
            <p className="text-[11px] text-qa-muted mt-1">Chatbot implementado con Arquitectura Agéntica</p>
          </div>

          {/* Escenario del Robot */}
          <div className="relative h-[62px] flex items-center justify-center overflow-hidden">
            <div className="absolute bottom-1 w-[120px] h-[30px] rounded-[50%] border border-qa-purple/60 shadow-[0_0_15px_rgba(142,53,255,0.4)]"></div>
            <div className="text-4xl filter drop-shadow-[0_0_12px_rgba(142,53,255,0.75)] z-10">🤖</div>
          </div>
        </div>

        {/* CAJA DE MENSAJES */}
        <div className="flex-1 bg-[#030618]/60 border border-qa-purple/30 rounded-xl overflow-y-auto p-4 mb-2 scrollbar-thin">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-[70px] h-[48px] border-4 border-qa-purple rounded-2xl flex items-center justify-center text-qa-purple-light text-2xl shadow-[0_0_20px_rgba(142,53,255,0.28)] mb-3 font-black">
                •••
              </div>
              <h3 className="text-lg font-bold text-white mb-1">Inicia una conversación</h3>
              <p className="text-qa-muted text-sm">Escribe tu mensaje para comenzar</p>
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
      </div>

      {/* TARJETA DE CONTROLES*/}
      <div className="bg-qa-panel/60 border-2 border-qa-purple/40 rounded-2xl p-3 flex flex-col gap-2 shadow-[0_0_15px_rgba(142,53,255,0.1)]">
        <p className="text-[10px] text-qa-muted">CSV opcional para ejecutar validaciones. Puedes conversar sin cargar archivo.</p>
        
        {/* Fila de Archivo */}
        <div className="flex gap-2">
          <div className="flex-1 bg-black/40 border border-qa-purple/30 rounded-xl px-3 py-2 flex items-center overflow-hidden">
            <span className="text-[11px] text-[#c9c3e8] truncate">
              {selectedFile 
                ? `Archivo cargado: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`
                : "No hay ningún archivo seleccionado..."}
            </span>
          </div>
          
          {/* Input de archivo oculto */}
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            className="hidden" 
            accept=".csv"
          />
          
          <button 
            className="w-10 bg-qa-bot-gradient rounded-xl font-bold hover:scale-110 active:scale-95 transition-all text-white shadow-[0_0_10px_rgba(142,53,255,0.3)]"
            onClick={() => fileInputRef.current.click()}
            title="Subir archivo CSV"
          >
            +
          </button>
        </div>

        {/* Input y Botones */}
        <div className="flex gap-2">
          <input
            className="flex-1 bg-qa-deep/90 border border-qa-purple/40 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-qa-purple transition-all placeholder:text-white/40"
            placeholder="Escribe tu mensaje aquí..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />

          <button 
            className="bg-gradient-to-r from-qa-purple to-[#5b13db] px-5 py-2 rounded-xl text-[11px] font-black text-white shadow-[0_0_15px_rgba(142,53,255,0.4)] hover:brightness-110 hover:scale-105 active:scale-95 transition-all uppercase"
            onClick={sendMessage}
          >
            ➤ Enviar
          </button>

          <button 
            className="bg-gradient-to-r from-[#6d28d9] to-[#35006f] px-5 py-2 rounded-xl text-[11px] font-black text-white hover:brightness-110 hover:scale-105 active:scale-95 transition-all uppercase"
            onClick={clearChat}
          >
            Limpiar
          </button>
        </div>
      </div>
    </main>
  );
}