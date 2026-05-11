import React, { useState } from "react";
import LeftPanel from "./components/LeftPanel";
import ChatPanel from "./components/ChatPanel";
import RightPanel from "./components/RightPanel";
import useQABotChat from "./hooks/useQABotChat";

export default function App() {
  // 1. Estados para la lógica de archivos y reportes
  const [selectedFile, setSelectedFile] = useState(null);
  const [lastReport, setLastReport] = useState(null);
  const [history, setHistory] = useState([]);

  // 2. Hook del chat que maneja la lógica de mensajes, input y comunicación con la API
  const chat = useQABotChat(
    selectedFile, 
    (newReport) => {
      // Esta función se ejecuta cuando la API devuelve un resultado exitoso
      setLastReport(newReport);
      
      const historyEntry = {
        id: newReport.execution_id,
        icon: newReport.global_status === "PASS" ? "◈" : "⚠",
        title: `Análisis: ${newReport.global_status}`,
        date: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: newReport.global_status
      };

      setHistory((prev) => [historyEntry, ...prev.slice(0, 4)]); // Guardamos los últimos 5
    },
    setSelectedFile 
  );
  
  const BG_URL = "/QABotBackground.png";

  // Función para manejar la subida desde el ChatPanel
  const handleFileUpload = (file) => {
    setSelectedFile(file);
    console.log("Archivo listo para procesar:", file.name);
  };

  // Función para resetear todo el sistema (Nueva Sesión)
  const handleNewSession = () => {
    chat.newSession(); // Limpia mensajes e input en el hook
    setSelectedFile(null);
    setLastReport(null);
  };

  return (
    <div className="relative min-h-screen w-full bg-qa-deep overflow-hidden font-sans">
      {/* CAPA DE FONDO */}
      <div 
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat opacity-40"
        style={{ backgroundImage: `url(${BG_URL})` }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-r from-qa-deep via-transparent to-qa-deep opacity-90" />

      {/* CONTENEDOR PRINCIPAL: Grid de 3 columnas */}
      <div className="relative z-10 grid grid-cols-[280px_1fr_340px] gap-6 p-6 h-screen max-h-screen">
        
        {/* Panel Izquierdo: Acciones globales */}
        <LeftPanel onNewSession={handleNewSession} />
        
        {/* Panel Central: El chat interactivo */}
        <ChatPanel 
          messages={chat.messages}
          input={chat.input}
          setInput={chat.setInput}
          sendMessage={chat.sendMessage}
          clearChat={chat.clearChat}
          onFileUpload={handleFileUpload}
          selectedFile={selectedFile}
          isLoading={chat.isLoading}
        />
        
        {/* Panel Derecho: Métricas dinámicas y trazabilidad */}
        <RightPanel 
          history={history} 
          lastReport={lastReport} 
        />
      </div>
    </div>
  );
}