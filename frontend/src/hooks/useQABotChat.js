import { useState } from "react";

export default function useQABotChat(selectedFile, onReportGenerated, setSelectedFile, setDownloadEnabled) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    // Si no hay texto ni archivo, no hacemos nada
    if (!input.trim() && !selectedFile) return;

    setIsLoading(true);

    // 1. Crear el mensaje del usuario
    const userMsg = {
      role: "user",
      content: input || (selectedFile ? `Analiza el archivo ${selectedFile.name}` : ""),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    
    setMessages((prev) => [...prev, userMsg]);
    const currentInput = input;
    setInput(""); // Limpiamos el input de texto

    try {
      // 2. Preparar FormData
      const formData = new FormData();
      formData.append("user_message", currentInput || "Analiza este dataset");
      if (selectedFile) {
        formData.append("file", selectedFile);
      }

      // 3. Petición al Backend (FastAPI)
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Error en la respuesta del servidor");

      const data = await response.json();
      setDownloadEnabled(data.hasReport === true);

      // 4. Añadir respuesta del Bot a la conversación
      const botMsg = {
        role: "assistant",
        content: data.assistant_message,
        hasReport: data.hasReport,
        execution_id: data.execution_id, 
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);

      // 5. Procesar el Reporte para el RightPanel
      if (data.report?.results) {
        const calculatedMetrics = transformMetrics(data.report.results);
        
        // Creamos el objeto de reporte actualizado
        const fullReport = {
          ...data.report,
          metrics: calculatedMetrics
        };
        onReportGenerated(fullReport, data.addToHistory); 
      }

    } catch (error) {
      console.error("Error en QA Bot:", error);
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: "Error de conexión con el servidor de QA.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Transforma los ratios (0.01) en porcentajes (99%) para las barras de progreso
  const transformMetrics = (results) => {
    if (!results) return [];
    
    const metrics = [];

    results.forEach(res => {
      console.log(`[${res.name}] metrics:`, JSON.stringify(res.metrics, null, 2));
      const m = res.metrics?.metrics ?? res.metrics ?? {};

      if (res.name === "nulls") {
        const ratio = m.global_null_ratio ?? 0;
        metrics.push({
          label: "Calidad Nulos",
          value: Math.max(0, Math.round((1 - ratio) * 100))
        });
      }

      if (res.name === "duplicates") {
        const ratio = m.duplicate_ratio ?? 0;
        metrics.push({
          label: "Unicidad",
          value: Math.max(0, Math.round((1 - ratio) * 100))
        });
      }

      if (res.name === "outliers") {
        const ratios = Object.values(m.outlier_ratio_by_column ?? {});
        const avg = ratios.length > 0
          ? ratios.reduce((a, b) => a + b, 0) / ratios.length
          : 0;
        metrics.push({
          label: "Limpieza Outliers",
          value: Math.max(0, Math.round((1 - avg) * 100))
        });
      }

      if (res.name === "data_types") {
        const totalCols = m.total_columns ?? 1;
        const mismatches = res.metrics?.mismatches?.length ?? 0;
        metrics.push({
          label: "Consistencia Tipos",
          value: Math.max(0, Math.round(((totalCols - mismatches) / totalCols) * 100))
        });
      }
    });

    return metrics;
  };

  const clearChat = () => setMessages([]);
  
  const newSession = () => {
    setMessages([]);
    setInput("");
    if (setSelectedFile) setSelectedFile(null);
    if (setDownloadEnabled) setDownloadEnabled(false);
  };

  return { messages, input, setInput, sendMessage, clearChat, newSession, isLoading };
}