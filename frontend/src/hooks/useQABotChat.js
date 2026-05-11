import { useState } from "react";

export default function useQABotChat(selectedFile, onReportGenerated, setSelectedFile) {
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
        // Nota: No poner Content-Type manual, el navegador lo hace con el boundary
      });

      if (!response.ok) throw new Error("Error en la respuesta del servidor");

      const data = await response.json();

      // 4. Añadir respuesta del Bot a la conversación
      const botMsg = {
        role: "assistant",
        content: data.assistant_message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);

      // 5. Procesar el Reporte para el RightPanel
      if (data.report) {
        // Calculamos los porcentajes para las barras de MetricsCard
        const calculatedMetrics = transformMetrics(data.report.results);
        
        // Enviamos el reporte completo al estado global de la App
        onReportGenerated({
          ...data.report,
          metrics: calculatedMetrics // Sobrescribimos con las métricas calculadas (0-100)
        });
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
      // Test de Nulos
      if (res.name === "Nulos" && res.metrics?.global_null_ratio !== undefined) {
        metrics.push({ 
          label: "Calidad Nulos", 
          value: Math.max(0, (1 - res.metrics.global_null_ratio) * 100) 
        });
      }
      // Test de Duplicados
      if (res.name === "Duplicados" && res.metrics?.duplicate_ratio !== undefined) {
        metrics.push({ 
          label: "Unicidad", 
          value: Math.max(0, (1 - res.metrics.duplicate_ratio) * 100) 
        });
      }
      // Test de Outliers
      if (res.name === "Outliers" && res.metrics?.outlier_ratio_by_column) {
        const ratios = Object.values(res.metrics.outlier_ratio_by_column);
        const avgOutliers = ratios.length > 0 
          ? ratios.reduce((a, b) => a + b, 0) / ratios.length 
          : 0;
        metrics.push({ 
          label: "Limpieza Outliers", 
          value: Math.max(0, (1 - avgOutliers) * 100) 
        });
      }
    });

    // Si no hay métricas específicas, devolvemos un set por defecto para no romper el UI
    return metrics.length > 0 ? metrics : [
      { label: "Consistencia", value: 100 },
      { label: "Integridad", value: 100 }
    ];
  };

  const clearChat = () => setMessages([]);
  
  const newSession = () => {
    setMessages([]);
    setInput("");
    if (setSelectedFile) setSelectedFile(null);
  };

  return { messages, input, setInput, sendMessage, clearChat, newSession, isLoading };
}