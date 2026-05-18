import { useEffect, useState } from "react";

export default function useQABotChat(
  selectedFile,
  onReportGenerated,
  setSelectedFile,
  setDownloadEnabled,
  onSessionReportsRestored = null
) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [sessionId, setSessionId] = useState(
    localStorage.getItem("qabot_session_id")
  );

  const [availableSessions, setAvailableSessions] = useState([]);

  // Solicitud escrita por el usuario pero pendiente de artefacto.
  const [pendingPrompt, setPendingPrompt] = useState(null);

  // Criterio activo. Se reutiliza cuando el usuario sube una nueva versión del artefacto.
  const [activeReviewPrompt, setActiveReviewPrompt] = useState(null);

  // Último fichero procesado. Sirve para detectar nuevas versiones del artefacto.
  const [lastProcessedFileName, setLastProcessedFileName] = useState(null);

  const timestamp = () =>
    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const addMessage = (role, content, extra = {}) => {
    setMessages((prev) => [
      ...prev,
      {
        role,
        content,
        timestamp: timestamp(),
        ...extra,
      },
    ]);
  };

  const ensureServerSession = async () => {
    if (sessionId) return sessionId;

    const response = await fetch("http://localhost:8000/sessions", {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error("No se pudo crear el ciclo de pruebas en el servidor");
    }

    const data = await response.json();
    const newSessionId = data.session_id;

    setSessionId(newSessionId);
    localStorage.setItem("qabot_session_id", newSessionId);

    return newSessionId;
  };

  const loadAvailableSessions = async () => {
    try {
      const response = await fetch("http://localhost:8000/sessions");

      if (!response.ok) {
        console.warn("No se pudieron cargar los ciclos de pruebas.");
        return;
      }

      const data = await response.json();

      setAvailableSessions(data.sessions ?? []);
    } catch (error) {
      console.warn("Error cargando ciclos de pruebas:", error);
    }
  };

  const restoreSession = async (idToRestore, options = {}) => {
    const { silent = false } = options;
    const cleanSessionId = (idToRestore || "").trim();

    if (!cleanSessionId) {
      if (!silent) {
        alert("Introduce o selecciona un ciclo de pruebas para recuperar.");
      }

      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/sessions/${cleanSessionId}`
      );

      if (!response.ok) {
        if (!silent) {
          alert("No se pudo conectar con el servidor para recuperar el ciclo.");
        }

        return;
      }

      const data = await response.json();

      if (!data.found) {
        localStorage.removeItem("qabot_session_id");
        setSessionId(null);

        if (!silent) {
          alert(`No se ha encontrado el ciclo ${cleanSessionId}.`);
        }

        return;
      }

      const session = data.session;

      setSessionId(session.session_id);
      localStorage.setItem("qabot_session_id", session.session_id);

      setMessages(session.messages ?? []);
      setActiveReviewPrompt(session.active_review_prompt ?? null);
      setPendingPrompt(session.pending_prompt ?? null);
      setLastProcessedFileName(session.last_processed_file_name ?? null);

      if (session.reports?.length && onSessionReportsRestored) {
        const restoredReports = session.reports.map((report) => ({
          ...report,
          metrics: transformMetrics(report.results ?? []),
        }));

        onSessionReportsRestored(restoredReports);
      }

      if (session.last_report) {
        const calculatedMetrics = transformMetrics(
          session.last_report.results ?? []
        );

        onReportGenerated(
          {
            ...session.last_report,
            metrics: calculatedMetrics,
          },
          false
        );

        setDownloadEnabled(true);
      }

      if (!silent) {
        addMessage(
          "assistant",
          `He recuperado el ciclo <b>${session.session_id}</b>. Puedes continuar subiendo una nueva versión del dataset para relanzar las pruebas del ciclo activo.`
        );
      }

      await loadAvailableSessions();
    } catch (error) {
      console.error("Error recuperando ciclo:", error);

      if (!silent) {
        alert(
          "Error inesperado al recuperar el ciclo. Revisa la consola del navegador."
        );
      }
    }
  };

  useEffect(() => {
    const initialize = async () => {
      await loadAvailableSessions();

      const storedSessionId = localStorage.getItem("qabot_session_id");

      if (storedSessionId) {
        await restoreSession(storedSessionId, { silent: true });
      }
    };

    initialize();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const inferTestPhaseFromPrompt = (prompt) => {
    const text = (prompt || "").toLowerCase();

    // El orden es importante: algunos prompts de modelo o particiones contienen
    // palabras genéricas como "dataset" o "target". Por eso primero se evalúan
    // las fases más específicas y se deja la tabla minable como caso general.
    if (
      text.includes("particiones") ||
      text.includes("partición") ||
      text.includes("particion") ||
      text.includes("columna de partición") ||
      text.includes("columna de particion") ||
      text.includes("conjunto") ||
      text.includes("train") ||
      text.includes("training") ||
      text.includes("entrenamiento") ||
      text.includes("validación") ||
      text.includes("validacion") ||
      text.includes("split")
    ) {
      return "Particiones train/validation/test";
    }

    if (
      text.includes("umbral") ||
      text.includes("umbrales") ||
      text.includes("threshold") ||
      text.includes("punto de corte") ||
      text.includes("límite") ||
      text.includes("limite")
    ) {
      if (
        text.includes("desempeño") ||
        text.includes("rendimiento") ||
        text.includes("accuracy") ||
        text.includes("precision") ||
        text.includes("recall") ||
        text.includes("f1") ||
        text.includes("matriz de confusión") ||
        text.includes("matriz de confusion") ||
        text.includes("modelo")
      ) {
        return "Desempeño del modelo";
      }

      return "Scores y umbrales";
    }

    if (
      text.includes("accuracy") ||
      text.includes("precisión") ||
      text.includes("precision") ||
      text.includes("recall") ||
      text.includes("f1") ||
      text.includes("auc") ||
      text.includes("roc") ||
      text.includes("matriz de confusión") ||
      text.includes("matriz de confusion") ||
      text.includes("score") ||
      text.includes("probabilidad") ||
      text.includes("predicción") ||
      text.includes("prediccion") ||
      text.includes("modelo")
    ) {
      return "Desempeño del modelo";
    }

    if (
      text.includes("nulos") ||
      text.includes("duplicados") ||
      text.includes("outliers") ||
      text.includes("tipos") ||
      text.includes("balanceo") ||
      text.includes("tabla minable") ||
      text.includes("dataset")
    ) {
      return "Tabla minable";
    }

    return "Fase no determinada";
  };

  const getActiveSession = (sessionIdToFind = sessionId) => {
    return (
      availableSessions.find(
        (session) => session.session_id === sessionIdToFind
      ) || null
    );
  };

  const hasRequiredCycleMetadata = (sessionIdToCheck = sessionId) => {
    const activeSession = getActiveSession(sessionIdToCheck);

    return Boolean(activeSession?.project_label && activeSession?.review_label);
  };

  const updateCycleMetadata = async (metadata) => {
    const currentSessionId = await ensureServerSession();

    const normalizedMetadata = {
      project_label: metadata.project_label?.trim() || null,
      test_phase: metadata.test_phase?.trim() || null,
      review_label: metadata.review_label?.trim() || null,
    };

    const response = await fetch("http://localhost:8000/sessions/metadata", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: currentSessionId,
        ...normalizedMetadata,
      }),
    });

    if (!response.ok) {
      alert("No se pudieron guardar los datos del ciclo de pruebas.");
      return;
    }

    setAvailableSessions((prev) => {
      const existing = prev.find(
        (session) => session.session_id === currentSessionId
      );

      if (!existing) {
        return [
          {
            session_id: currentSessionId,
            ...normalizedMetadata,
            title: normalizedMetadata.review_label || "Ciclo de pruebas",
            iteration_count: 0,
            last_status: null,
          },
          ...prev,
        ];
      }

      return prev.map((session) =>
        session.session_id === currentSessionId
          ? {
              ...session,
              ...normalizedMetadata,
              title: normalizedMetadata.review_label || session.title,
            }
          : session
      );
    });

    await loadAvailableSessions();
  };

  const reportPhaseFeedback = async ({ detected_phase, comment }) => {
    const currentSessionId = await ensureServerSession();

    const prompt = activeReviewPrompt || pendingPrompt || input || "";

    const response = await fetch(
      "http://localhost:8000/sessions/phase-feedback",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          prompt,
          detected_phase,
          comment,
        }),
      }
    );

    if (!response.ok) {
      alert("No se pudo registrar la incidencia de fase.");
      return;
    }

    const assistantContent =
      "He registrado la incidencia de clasificación de fase. Esta información se utilizará para mejorar futuras versiones del intérprete de solicitudes.";

    addMessage("assistant", assistantContent);

    await fetch("http://localhost:8000/sessions/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: currentSessionId,
        role: "assistant",
        content: assistantContent,
        timestamp: timestamp(),
      }),
    });
  };

  const runAssessment = async ({
    promptToRun,
    fileToUse,
    autoTriggered = false,
    reason = null,
  }) => {
    const cleanPrompt = (promptToRun || "").trim();

    if (!cleanPrompt) return;

    // Caso 1: no hay artefacto. Guardamos el criterio de pruebas activo.
    if (!fileToUse) {
      const currentSessionId = await ensureServerSession();

      setPendingPrompt(cleanPrompt);
      setActiveReviewPrompt(cleanPrompt);
      setDownloadEnabled(false);

      const detectedPhase = inferTestPhaseFromPrompt(cleanPrompt);

      const assistantContent = `
He registrado tu solicitud de ejecución de una nueva iteración del ciclo de pruebas activo, pero falta el artefacto de datos.

He identificado la fase de pruebas como: <b>${detectedPhase}</b>.

Antes de ejecutar la primera iteración, completa los datos obligatorios del ciclo:
<ul>
  <li>Proyecto</li>
  <li>Título del ciclo</li>
</ul>

Cuando subas un dataset, relanzaré automáticamente las pruebas si el ciclo está configurado.
`;

      addMessage("assistant", assistantContent);

      await fetch("http://localhost:8000/sessions/state", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          active_review_prompt: cleanPrompt,
          pending_prompt: cleanPrompt,
          last_processed_file_name: lastProcessedFileName,
        }),
      });

      await fetch("http://localhost:8000/sessions/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          role: "user",
          content: cleanPrompt,
          timestamp: timestamp(),
        }),
      });

      await fetch("http://localhost:8000/sessions/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          role: "assistant",
          content: assistantContent,
          timestamp: timestamp(),
        }),
      });

      await loadAvailableSessions();

      return;
    }

    if (isLoading) return;

    try {
      const currentSessionId = await ensureServerSession();

      // Caso 2: hay artefacto, pero el ciclo no está configurado.
      if (!hasRequiredCycleMetadata(currentSessionId)) {
        addMessage(
          "assistant",
          "Antes de ejecutar la primera iteración debes completar los datos obligatorios del ciclo de pruebas: proyecto y título del ciclo."
        );

        return;
      }

      setIsLoading(true);

      if (autoTriggered) {
        const explanation =
          reason === "pending_prompt"
            ? "He detectado una iteración de pruebas pendiente de ejecutar por no disponer del dataset que se acaba de aportar. Una vez resuelto el problema, relanzamos automáticamente la ejecución de las pruebas de la iteración."
            : "He detectado una nueva versión del artefacto. Lanzamos la ejecución de una nueva iteración del ciclo de pruebas activo.";

        addMessage("assistant", explanation);
      }

      const formData = new FormData();
      formData.append("user_message", cleanPrompt);
      formData.append("session_id", currentSessionId);
      formData.append("file", fileToUse);

      await addProgressMessages();

      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Error en la respuesta del servidor");
      }

      const data = await response.json();

      setDownloadEnabled(data.hasReport === true);

      await addAssistantMessageProgressively(data.assistant_message, {
        hasReport: data.hasReport,
        execution_id: data.execution_id,
      });

      if (data.report?.results) {
        const calculatedMetrics = transformMetrics(data.report.results);

        const fullReport = {
          ...data.report,
          metrics: calculatedMetrics,
        };

        onReportGenerated(fullReport, data.addToHistory);
      }

      if (data.report) {
        setPendingPrompt(null);
        setActiveReviewPrompt(cleanPrompt);
        setLastProcessedFileName(fileToUse.name);
      }

      await loadAvailableSessions();
    } catch (error) {
      console.error("Error en QA Bot:", error);

      addMessage(
        "assistant",
        "Error de conexión con el servidor de pruebas. Revisa que el backend esté arrancado."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    const promptToRun = input.trim();

    // Si no hay texto ni archivo, no hacemos nada.
    if (!promptToRun && !selectedFile) return;

    // Si el usuario solo sube un archivo y ya hay ciclo de pruebas activo,
    // no hace falta inventar un prompt genérico.
    if (!promptToRun && selectedFile && activeReviewPrompt) {
      await runAssessment({
        promptToRun: activeReviewPrompt,
        fileToUse: selectedFile,
        autoTriggered: true,
        reason: "new_artifact_version",
      });

      return;
    }

    const displayedUserMessage =
      promptToRun || (selectedFile ? `Analiza el archivo ${selectedFile.name}` : "");

    addMessage("user", displayedUserMessage);

    setInput("");

    await runAssessment({
      promptToRun: promptToRun || activeReviewPrompt || "Analiza este dataset",
      fileToUse: selectedFile,
      autoTriggered: false,
    });
  };

  const handleDatasetUploaded = async (file) => {
    if (!file) return;

    if (setSelectedFile) {
      setSelectedFile(file);
    }

    const isDifferentFile = lastProcessedFileName !== file.name;

    // Caso 1: había un prompt pendiente porque faltaba dataset.
    if (pendingPrompt) {
      await runAssessment({
        promptToRun: pendingPrompt,
        fileToUse: file,
        autoTriggered: true,
        reason: "pending_prompt",
      });

      return;
    }

    // Caso 2: ya existe un ciclo de pruebas activo y se sube una nueva versión del artefacto.
    if (activeReviewPrompt && isDifferentFile) {
      await runAssessment({
        promptToRun: activeReviewPrompt,
        fileToUse: file,
        autoTriggered: true,
        reason: "new_artifact_version",
      });
    }
  };

  // Transforma los ratios en porcentajes para las barras de progreso.
  const transformMetrics = (results) => {
    if (!results) return [];

    const metrics = [];

    results.forEach((res) => {
      const m = res.metrics?.metrics ?? res.metrics ?? {};

      if (res.name === "nulls") {
        const ratio = m.global_null_ratio ?? 0;

        metrics.push({
          label: "Calidad Nulos",
          value: Math.max(0, Math.round((1 - ratio) * 100)),
        });
      }

      if (res.name === "duplicates") {
        const ratio = m.duplicate_ratio ?? 0;

        metrics.push({
          label: "Unicidad",
          value: Math.max(0, Math.round((1 - ratio) * 100)),
        });
      }

      if (res.name === "outliers") {
        const ratios = Object.values(m.outlier_ratio_by_column ?? {});
        const avg =
          ratios.length > 0
            ? ratios.reduce((a, b) => a + b, 0) / ratios.length
            : 0;

        metrics.push({
          label: "Limpieza Outliers",
          value: Math.max(0, Math.round((1 - avg) * 100)),
        });
      }

      if (res.name === "data_types") {
        const totalCols = m.total_columns ?? 1;
        const mismatches = res.metrics?.mismatches?.length ?? 0;

        metrics.push({
          label: "Consistencia Tipos",
          value: Math.max(
            0,
            Math.round(((totalCols - mismatches) / totalCols) * 100)
          ),
        });
      }

      if (res.name === "balance") {
        const majorityRatio = m.majority_class_ratio ?? 0;
        const balanceQuality = Math.max(
          0,
          Math.round((1 - Math.max(0, majorityRatio - 0.5)) * 100)
        );

        metrics.push({
          label: "Balanceo",
          value: balanceQuality,
        });
      }

      if (res.name === "model_performance") {
        const modelMetricMap = [
          ["Accuracy Modelo", m.accuracy],
          ["Precision Modelo", m.precision],
          ["Recall Modelo", m.recall],
          ["F1 Modelo", m.f1],
          ["ROC AUC", m.roc_auc],
        ];

        modelMetricMap.forEach(([label, value]) => {
          if (typeof value === "number") {
            metrics.push({
              label,
              value: Math.max(0, Math.min(100, Math.round(value * 100))),
            });
          }
        });
      }

      if (res.name === "dataset_split") {
        const missing = m.missing_splits?.length ?? 0;
        const unknown = m.unknown_splits?.length ?? 0;
        const duplicateIds = m.duplicate_ids_across_splits ?? 0;
        const deltas = Object.values(m.target_distribution_deltas ?? {});
        const maxTargetDelta = deltas.length > 0 ? Math.max(...deltas) : 0;
        const splitRatios = Object.values(m.split_ratios ?? {});
        const minSplitRatio = splitRatios.length > 0 ? Math.min(...splitRatios) : 0;

        const partitionCoverage = Math.max(0, 100 - missing * 34);
        const labelConsistency = unknown === 0 ? 100 : Math.max(0, 100 - unknown * 25);
        const noLeakage = duplicateIds === 0 ? 100 : 0;
        const targetStability = Math.max(0, Math.round((1 - maxTargetDelta) * 100));
        const splitSizeQuality = Math.max(0, Math.min(100, Math.round(minSplitRatio * 500)));

        metrics.push({
          label: "Cobertura Particiones",
          value: partitionCoverage,
        });

        metrics.push({
          label: "Etiquetas Split",
          value: labelConsistency,
        });

        metrics.push({
          label: "Sin Fuga IDs",
          value: noLeakage,
        });

        if (deltas.length > 0) {
          metrics.push({
            label: "Estabilidad Target",
            value: targetStability,
          });
        }

        if (splitRatios.length > 0) {
          metrics.push({
            label: "Tamaño Particiones",
            value: splitSizeQuality,
          });
        }
      }
    });

    return metrics;
  };

  const clearChat = () => {
    setMessages([]);
    setInput("");
  };

  const clearActiveReview = () => {
    setPendingPrompt(null);
    setActiveReviewPrompt(null);
    setLastProcessedFileName(null);
    setInput("");

    if (setDownloadEnabled) {
      setDownloadEnabled(false);
    }
  };

  const newSession = () => {
    setMessages([]);
    setInput("");
    setPendingPrompt(null);
    setActiveReviewPrompt(null);
    setLastProcessedFileName(null);

    if (setSelectedFile) {
      setSelectedFile(null);
    }

    if (setDownloadEnabled) {
      setDownloadEnabled(false);
    }

    localStorage.removeItem("qabot_session_id");
    setSessionId(null);
  };

  const addProgressMessages = async () => {
    const steps = [
      "Interpretando solicitud de pruebas...",
      "Validando artefactos aportados...",
      "Generando plan de pruebas...",
      "Ejecutando pruebas de calidad...",
      "Recopilando defectos y evidencias...",
      "Generando informe de pruebas...",
    ];

    for (const step of steps) {
      addMessage("assistant", `<span class="text-qa-muted">${step}</span>`);
      await new Promise((resolve) => setTimeout(resolve, 350));
    }
  };

  const addAssistantMessageProgressively = async (htmlContent, extra = {}) => {
    const safeHtmlContent = htmlContent || "";

    const messageId = `msg-${Date.now()}-${Math.random()
      .toString(16)
      .slice(2)}`;

    setMessages((prev) => [
      ...prev,
      {
        id: messageId,
        role: "assistant",
        content: "",
        timestamp: timestamp(),
        ...extra,
      },
    ]);

    const chunkSize = 18;
    let current = "";

    for (let i = 0; i < safeHtmlContent.length; i += chunkSize) {
      current += safeHtmlContent.slice(i, i + chunkSize);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? {
                ...msg,
                content: current,
              }
            : msg
        )
      );

      await new Promise((resolve) => setTimeout(resolve, 12));
    }
  };

  return {
    messages,
    input,
    setInput,
    sendMessage,
    clearChat,
    clearActiveReview,
    newSession,
    isLoading,
    handleDatasetUploaded,
    pendingPrompt,
    activeReviewPrompt,
    sessionId,
    restoreSession,
    availableSessions,
    loadAvailableSessions,
    updateCycleMetadata,
    inferTestPhaseFromPrompt,
    reportPhaseFeedback,
  };
}