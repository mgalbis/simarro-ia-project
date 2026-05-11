import React from "react";

export default function LeftPanel({ onNewSession }) {
  return (
    <aside className="bg-qa-panel border border-qa-border rounded-[22px] backdrop-blur-xl shadow-[0_0_25px_rgba(142,53,255,0.25)] p-4 flex flex-col gap-5 h-full overflow-y-auto">
      
      {/* TÍTULO: LIMITACIONES */}
      <div className="flex items-center gap-2 text-qa-purple-light font-[900] text-[12px] tracking-[0.15em] uppercase">
        <div className="w-5 h-5 border border-qa-purple-light rounded-full flex items-center justify-center text-[10px] font-bold">
          i
        </div>
        LIMITACIONES
      </div>

      {/* CAJA DE CONTENIDO PRINCIPAL */}
      <div className="bg-[#0c0d21]/50 border border-qa-border-glow rounded-[20px] p-4 flex flex-col gap-4">
        
        {/* CABECERA CON ICONO BOT */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-qa-bot-gradient rounded-[14px] flex items-center justify-center text-2xl shadow-[0_0_15px_rgba(142,53,255,0.4)]">
            🤖
          </div>
          <div className="leading-tight">
            <span className="text-[13px] font-black text-white block uppercase tracking-tight">QABot en fase</span>
            <span className="text-[13px] font-black text-white block uppercase tracking-tight">de mejora</span>
          </div>
        </div>

        <p className="text-[11.5px] text-qa-muted leading-relaxed font-medium">
          Soy QABot, un asistente agéntico de calidad impulsado por arquitectura agéntica.
        </p>

        {/* DIVISOR TÉCNICO */}
        <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-qa-purple/30 to-transparent"></div>

        {/* LISTA DE LIMITACIONES */}
        <ul className="flex flex-col gap-3">
          {[
            "Puedo cometer errores.",
            "Mi conocimiento puede estar desactualizado.",
            "No tengo acceso en tiempo real a internet.",
            "No realizo acciones externas ni accedo a sistemas privados.",
            "Estoy en constante aprendizaje para ofrecerte mejores respuestas."
          ].map((text, index) => (
            <li key={index} className="flex gap-2 items-start">
              <span className="text-qa-magenta text-[14px] leading-[14px] mt-0.5">●</span>
              <span className="text-[11px] text-[#f3f1ff] leading-snug">{text}</span>
            </li>
          ))}
        </ul>

        <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-qa-purple/30 to-transparent"></div>

        <p className="text-[10.5px] text-qa-purple-light italic font-semibold">
          ★ Gracias por tu comprensión y por ayudarme a mejorar cada día.
        </p>
      </div>

      {/* SECCIÓN NUEVA SESIÓN (Push to bottom) */}
      <div className="mt-auto pt-4 border-t border-qa-border/20">
        <div className="text-qa-purple-light font-black text-[11px] tracking-widest uppercase mb-3 text-center">
          NUEVA CONVERSACIÓN
        </div>

        <button
          className="w-full bg-gradient-to-r from-qa-purple to-[#4300a3] py-3 rounded-xl font-[900] text-[12px] text-white shadow-[0_0_18px_rgba(142,53,255,0.3)] hover:scale-[1.02] active:scale-95 transition-all uppercase tracking-wider"
          onClick={() => onNewSession?.()}
        >
          ＋ Nueva sesión
        </button>
      </div>
    </aside>
  );
}