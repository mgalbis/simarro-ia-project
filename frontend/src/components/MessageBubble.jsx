export default function MessageBubble({ role, content, timestamp }) {
  const isUser = role === "user";

  return (
    <div className={`flex w-full mb-6 ${isUser ? "justify-end" : "justify-start"}`}>

      {!isUser && (
        <div className="flex-shrink-0 w-9 h-9 rounded-2xl bg-qa-bot-gradient flex items-center justify-center shadow-[0_0_15px_rgba(142,53,255,0.4)] mr-3 mt-1 overflow-hidden border border-white/10">
          <img src="/QABotIcon.png" alt="Bot" className="w-full h-full object-contain scale-105" />
        </div>
      )}

      <div className={`relative max-w-[85%] px-4 py-3 rounded-[20px] text-[13.5px] leading-relaxed transition-all ${
        isUser
          ? "bg-qa-purple text-white rounded-tr-none border border-white/10 shadow-[0_5px_15px_rgba(0,0,0,0.2)]"
          : "bg-[#1a1a2e]/80 text-[#f3f1ff] rounded-tl-none border border-qa-purple/30 backdrop-blur-md shadow-[0_5px_20px_rgba(0,0,0,0.3)]"
      }`}>

        <div className="break-words font-medium">
          {isUser
            ? <div>{content}</div>
            : <div className="prose prose-invert max-w-none" dangerouslySetInnerHTML={{ __html: content }} />
          }
        </div>

        <div className={`flex items-center gap-1 mt-2 text-[9px] font-bold uppercase tracking-tighter ${
          isUser ? "text-white/60 justify-end" : "text-qa-muted justify-start"
        }`}>
          {timestamp}
          {isUser && <span className="text-[#10b981] ml-1 font-black">✓✓</span>}
        </div>

        <div className={`absolute top-0 w-3 h-3 ${
          isUser
            ? "right-[-5px] border-l-[8px] border-l-qa-purple border-b-[8px] border-b-transparent"
            : "left-[-5px] border-r-[8px] border-r-qa-purple/30 border-b-[8px] border-b-transparent"
        }`} />
      </div>
    </div>
  );
}