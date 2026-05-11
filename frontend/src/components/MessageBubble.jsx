import React from "react";

export default function MessageBubble({
  role,
  content,
  timestamp,
}) {
  const isUser = role === "user";

  return (
    <div className={`flex w-full mb-4 ${isUser ? "justify-end" : "justify-start"}`}>
      
      {/* AVATAR DEL BOT */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-qa-bot-gradient flex items-center justify-center text-sm shadow-[0_0_10px_rgba(142,53,255,0.4)] mr-3 mt-1">
          🤖
        </div>
      )}

      {/* BURBUJA DE MENSAJE */}
      <div
        className={`relative max-w-[80%] px-4 py-3 rounded-[18px] text-[13.5px] leading-relaxed shadow-sm transition-all ${
          isUser
            ? "bg-qa-purple text-white rounded-tr-none border border-white/10"
            : "bg-slate-800/60 text-[#f3f1ff] rounded-tl-none border border-qa-border-glow backdrop-blur-md"
        }`}
      >
        {/* CONTENIDO */}
        <div className="break-words font-medium">
          {isUser ? (
            <div>{content}</div>
          ) : (
            <div
              className="prose prose-invert max-w-none"
              dangerouslySetInnerHTML={{
                __html: content,
              }}
            />
          )}
        </div>

        {/* TIMESTAMP Y CHECK */}
        <div 
          className={`flex items-center gap-1 mt-1.5 text-[9px] font-bold uppercase tracking-tighter ${
            isUser ? "text-white/60 justify-end" : "text-qa-muted justify-start"
          }`}
        >
          {timestamp}
          {isUser && <span className="text-qa-green ml-1 font-black">✓✓</span>}
        </div>
        
        {/* FLECHITA DE LA BURBUJA */}
        <div 
          className={`absolute top-0 w-2 h-2 ${
            isUser 
              ? "right-[-4px] border-l-[6px] border-l-qa-purple border-b-[6px] border-b-transparent" 
              : "left-[-4px] border-r-[6px] border-r-qa-border-glow border-b-[6px] border-b-transparent"
          }`}
        />
      </div>
    </div>
  );
}