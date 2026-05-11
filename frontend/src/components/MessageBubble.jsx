import React from "react";

export default function MessageBubble({
  role,
  content,
  timestamp,
  execution_id,
  hasReport
}) {
  const isUser = role === "user";

  const handleDownload = () => {
    // Abrimos la URL en una pestaña nueva, lo que disparará la descarga automática
    window.open(`http://localhost:8000/download/${execution_id}`, "_blank");
  };

  return (
    <div className={`flex w-full mb-6 ${isUser ? "justify-end" : "justify-start"}`}>
      
      {/* AVATAR DEL BOT */}
      {!isUser && (
        <div className="flex-shrink-0 w-9 h-9 rounded-2xl bg-qa-bot-gradient flex items-center justify-center shadow-[0_0_15px_rgba(142,53,255,0.4)] mr-3 mt-1 overflow-hidden border border-white/10">
          <img 
            src="/QABotIcon.png" 
            alt="Bot" 
            className="w-full h-full object-contain scale-105" 
          />
        </div>
      )}

      {/* BURBUJA DE MENSAJE */}
      <div
        className={`relative max-w-[85%] px-4 py-3 rounded-[20px] text-[13.5px] leading-relaxed transition-all ${
          isUser
            ? "bg-qa-purple text-white rounded-tr-none border border-white/10 shadow-[0_5px_15px_rgba(0,0,0,0.2)]"
            : "bg-[#1a1a2e]/80 text-[#f3f1ff] rounded-tl-none border border-qa-purple/30 backdrop-blur-md shadow-[0_5px_20px_rgba(0,0,0,0.3)]"
        }`}
      >
        {/* CONTENIDO */}
        <div className="break-words font-medium">
          {isUser ? (
            <div>{content}</div>
          ) : (
            <>
              <div
                className="prose prose-invert max-w-none"
                dangerouslySetInnerHTML={{
                  __html: content,
                }}
              />
              
              {/* BOTÓN DE DESCARGA */}
              {hasReport && (
                <div className="mt-4 pt-3 border-t border-white/10">
                  <button 
                    onClick={handleDownload}
                    className="flex items-center justify-center gap-2 w-full bg-gradient-to-r from-[#4f46e5] to-[#7c3aed] hover:from-[#4338ca] hover:to-[#6d28d9] text-white font-black py-2.5 rounded-xl text-[11px] uppercase tracking-wider shadow-[0_0_15px_rgba(124,58,237,0.3)] transition-all hover:scale-[1.02] active:scale-95"
                  >
                    <span>Descargar Informe QA</span>
                    <span className="text-sm">📥</span>
                  </button>
                  <p className="text-[9px] text-qa-muted mt-2 text-center italic">
                    El documento incluye el análisis detallado de nulos, duplicados y outliers.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* TIMESTAMP Y CHECK */}
        <div 
          className={`flex items-center gap-1 mt-2 text-[9px] font-bold uppercase tracking-tighter ${
            isUser ? "text-white/60 justify-end" : "text-qa-muted justify-start"
          }`}
        >
          {timestamp}
          {isUser && <span className="text-[#10b981] ml-1 font-black">✓✓</span>}
        </div>
        
        <div 
          className={`absolute top-0 w-3 h-3 ${
            isUser 
              ? "right-[-5px] border-l-[8px] border-l-qa-purple border-b-[8px] border-b-transparent" 
              : "left-[-5px] border-r-[8px] border-r-qa-purple/30 border-b-[8px] border-b-transparent"
          }`}
        />
      </div>
    </div>
  );
}