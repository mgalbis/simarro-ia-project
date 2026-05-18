import React from "react";

export default function MessageBubble({
  role = "assistant",
  content = "",
  timestamp = "",
}) {
  const isUser = role === "user";

  const decorateQaHtml = (html = "") => html;

  return (
    <div
      className={`flex w-full ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`flex gap-3 ${
          isUser
            ? "max-w-[72%] flex-row-reverse"
            : "w-full max-w-[94%]"
        }`}
      >
        {!isUser && (
          <div className="shrink-0 w-8 h-8 rounded-full bg-qa-bot-gradient shadow-[0_0_18px_rgba(142,53,255,0.65)] flex items-center justify-center mt-1">
            <img
              src="/QABotIcon.png"
              alt="QABot"
              className="w-full h-full object-contain scale-105"
            />
          </div>
        )}

        <div
          className={`relative rounded-2xl px-4 py-3 border text-[12px] leading-relaxed ${
            isUser
              ? "bg-gradient-to-r from-qa-purple to-[#7c3aed] text-white border-qa-purple/40 shadow-[0_0_18px_rgba(142,53,255,0.35)]"
              : "w-full bg-[#151428]/90 text-white/90 border-qa-purple/40 shadow-[0_0_18px_rgba(142,53,255,0.16)]"
          }`}
        >
          <div
            className="prose prose-invert max-w-none text-[12px] leading-relaxed"
            dangerouslySetInnerHTML={{ __html: decorateQaHtml(content) }}
          />

          {timestamp && (
            <div
              className={`mt-2 text-[9px] ${
                isUser ? "text-white/70 text-right" : "text-white/45"
              }`}
            >
              {timestamp}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}