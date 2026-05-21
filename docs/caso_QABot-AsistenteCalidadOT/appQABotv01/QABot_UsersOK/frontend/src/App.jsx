import React, { useState } from "react";
import LeftPanel from "./components/LeftPanel";
import ChatPanel from "./components/ChatPanel";
import RightPanel from "./components/RightPanel";
import useQABotChat from "./hooks/useQABotChat";

export default function App({ user, onLogout }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [lastReport, setLastReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [downloadEnabled, setDownloadEnabled] = useState(false);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  
  const BG_URL = "/QABotBackground.png";

  // Función para manejar la subida desde el ChatPanel
  const handleFileUpload = (file) => {
    console.log("Archivo listo para procesar:", file.name);
    chat.handleDatasetUploaded(file);
  };

  // Función para resetear todo el sistema y crear un nuevo ciclo
  const handleNewSession = () => {
    chat.newSession();
    setSelectedFile(null);
    setLastReport(null);
    setHistory([]);
    setDownloadEnabled(false);
  };

  const handleOpenHistoricalReport = (report) => {
    if (!report) return;

    setLastReport(report);
    setDownloadEnabled(true);
  };

  const handleSessionReportsRestored = (reports) => {
    if (!reports?.length) return;

    const restoredHistory = reports.map((report, index) => ({
      id: report.execution_id,
      execution_id: report.execution_id,
      iterationNumber: reports.length - index,
      fileName:
        report.quality_assessment_order?.artifacts?.dataset?.name ||
        "Dataset recuperado",
      date: "Histórico",
      time: report.execution_id || "",
      status: report.global_status,
      report,
    }));

    setHistory(restoredHistory);
  };

  const chat = useQABotChat(
    selectedFile, 
    (newReport, shouldAddToHistory = true) => {
      setLastReport(newReport);

      if (shouldAddToHistory) {
        const now = new Date();

        setHistory((prev) => {
          const historyEntry = {
            id: newReport.execution_id,
            execution_id: newReport.execution_id,
            iterationNumber: prev.length + 1,
            fileName: selectedFile?.name || "Dataset",
            date: now.toLocaleDateString(),
            time: now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            status: newReport.global_status,
            report: newReport,
          };

          return [historyEntry, ...prev];
        });
      }
    },
    setSelectedFile,
    setDownloadEnabled,
    handleSessionReportsRestored,
    user
  );

  const gridTemplateColumns = `${leftCollapsed ? "64px" : "320px"} minmax(620px, 1fr) ${
  rightCollapsed ? "64px" : "360px"
}`;

  return (
    <div className="relative h-screen max-h-screen overflow-hidden">
      {/* CAPA DE FONDO */}
      <div 
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat opacity-40"
        style={{ backgroundImage: `url(${BG_URL})` }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-r from-qa-deep via-transparent to-qa-deep opacity-90" />

      {/* CONTENEDOR PRINCIPAL */}
      <div
        className="relative z-10 grid gap-6 p-6 h-screen max-h-screen transition-all duration-300"
        style={{ gridTemplateColumns }}
      >
        {/* Panel Izquierdo: ciclos de pruebas y limitaciones */}
        <LeftPanel
          onNewSession={handleNewSession}
          sessions={chat.availableSessions}
          sessionId={chat.sessionId}
          onRestoreSession={chat.restoreSession}
          isCollapsed={leftCollapsed}
          onToggleCollapse={() => setLeftCollapsed((value) => !value)}
        />
        
        {/* Panel Central: Chat interactivo */}
        <ChatPanel 
          messages={chat.messages}
          input={chat.input}
          setInput={chat.setInput}
          sendMessage={chat.sendMessage}
          clearChat={chat.clearChat}
          clearActiveReview={chat.clearActiveReview}
          onFileUpload={handleFileUpload}
          selectedFile={selectedFile}
          isLoading={chat.isLoading}
          lastReport={lastReport} 
          downloadEnabled={downloadEnabled}
          activeReviewPrompt={chat.activeReviewPrompt}
          pendingPrompt={chat.pendingPrompt}
          sessionId={chat.sessionId}
          availableSessions={chat.availableSessions}
          onUpdateCycleMetadata={chat.updateCycleMetadata}
          inferTestPhaseFromPrompt={chat.inferTestPhaseFromPrompt}
          onReportPhaseFeedback={chat.reportPhaseFeedback}
          user={user}
          onLogout={onLogout}
        />
        
        {/* Panel Derecho: Iteraciones, última ejecución e indicadores */}
        <RightPanel 
          history={history} 
          lastReport={lastReport}
          onOpenHistoricalReport={handleOpenHistoricalReport}
          isCollapsed={rightCollapsed}
          onToggleCollapse={() => setRightCollapsed((value) => !value)}
          user={user}
        />
      </div>
    </div>
  );
}