import { useEffect, useState } from "react";
import { API_BASE } from "../config/api";

export default function useQABotChat(
  selectedFile,
  onReportGenerated,
  setSelectedFile,
  setDownloadEnabled,
  onSessionReportsRestored = null,
  user
) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const USER_ID = user?.id;

  const sessionStorageKey = USER_ID
    ? `qabot_session_id_${USER_ID}`
    : "qabot_session_id";

  const [sessionId, setSessionId] = useState(
    localStorage.getItem(sessionStorageKey)
  );

  const [availableSessions, setAvailableSessions] = useState([]);

  // Solicitud escrita por el usuario pero pendiente de artefacto.
  const [pendingPrompt, setPendingPrompt] = useState(null);

  // Criterio activo. Se reutiliza cuando el usuario sube una nueva versión del artefacto.
  const [activeReviewPrompt, setActiveReviewPrompt] = useState(null);

  // Último fichero procesado. Sirve para detectar nuevas versiones del artefacto.
  const [lastProcessedFileName, setLastProcessedFileName] = useState(null);

  // Último análisis conceptual usado como memoria funcional del ciclo.
  const [conceptualAnalysis, setConceptualAnalysis] = useState(null);

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
    if (!USER_ID) {
      throw new Error("No hay usuario autenticado para crear el ciclo de pruebas.");
    }

    if (sessionId) return sessionId;

    const response = await fetch(`${API_BASE}/sessions?user_id=${USER_ID}`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error("No se pudo crear el ciclo de pruebas en el servidor");
    }

    const data = await response.json();
    const newSessionId = data.session_id;

    setSessionId(newSessionId);
    localStorage.setItem(sessionStorageKey, newSessionId);

    return newSessionId;
  };

  const loadAvailableSessions = async () => {
    if (!USER_ID) return;

    try {
      const response = await fetch(`${API_BASE}/sessions?user_id=${USER_ID}`);

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

    if (!USER_ID) return;
    const cleanSessionId = (idToRestore || "").trim();

    if (!cleanSessionId) {
      if (!silent) {
        alert("Introduce o selecciona un ciclo de pruebas para recuperar.");
      }

      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/sessions/${cleanSessionId}?user_id=${USER_ID}`
      );

      if (!response.ok) {
        if (!silent) {
          alert("No se pudo conectar con el servidor para recuperar el ciclo.");
        }

        return;
      }

      const data = await response.json();

      if (!data.found) {
        localStorage.removeItem(sessionStorageKey);
        setSessionId(null);

        if (!silent) {
          alert(`No se ha encontrado el ciclo ${cleanSessionId}.`);
        }

        return;
      }

      const session = data.session;

      setSessionId(session.session_id);
      localStorage.setItem(sessionStorageKey, session.session_id);

      setMessages(session.messages ?? []);
      setActiveReviewPrompt(session.active_review_prompt ?? null);
      setPendingPrompt(session.pending_prompt ?? null);
      setLastProcessedFileName(session.last_processed_file_name ?? null);
      setConceptualAnalysis(null);

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
    if (!USER_ID) return;

    const initialize = async () => {
      await loadAvailableSessions();

      const storedSessionId = localStorage.getItem(sessionStorageKey);

      if (storedSessionId) {
        await restoreSession(storedSessionId, { silent: true });
      }
    };

    initialize();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [USER_ID]);

  const inferTestPhaseFromPrompt = (prompt) => {
    const text = (prompt || "").toLowerCase();

    // Mejora documental aislada: solo aplica cuando el prompt llega con una directiva explícita desde el DC.
    // El comportamiento legacy de inferencia por revisión/dataset queda intacto.
    if (text.includes("activity_type=minable_dataset_validation") || text.includes("actividad seleccionada: minable_dataset_validation")) {
      return "Validación de tabla minable";
    }
    if (text.includes("activity_type=dataset_split_validation") || text.includes("actividad seleccionada: dataset_split_validation")) {
      return "Particiones train/validation/test";
    }
    if (text.includes("activity_type=model_performance_evaluation") || text.includes("actividad seleccionada: model_performance_evaluation")) {
      return "Desempeño del modelo";
    }
    if (text.includes("activity_type=threshold_quality_evaluation") || text.includes("actividad seleccionada: threshold_quality_evaluation")) {
      return "Scores y umbrales";
    }

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

    const response = await fetch(`${API_BASE}/sessions/metadata`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: currentSessionId,
        user_id: USER_ID,
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
      `${API_BASE}/sessions/phase-feedback`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          user_id: USER_ID,
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

    await fetch(`${API_BASE}/sessions/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: currentSessionId,
        user_id: USER_ID,
        role: "assistant",
        content: assistantContent,
        timestamp: timestamp(),
      }),
    });
  };

  const buildPromptFromConceptualActivity = (activityType, originalPrompt = "") => {
    const selectedActivity = conceptualAnalysis?.supported_activities?.find(
      (activity) => activity.activity_type === activityType
    );

    const tests = selectedActivity?.tests || [];
    const rules = conceptualAnalysis?.business_rules || [];
    const metrics = conceptualAnalysis?.metrics || [];
    const datasets = conceptualAnalysis?.datasets || [];

    const basePrompt = selectedActivity
      ? [
          `activity_type=${selectedActivity.activity_type}`,
          `Actividad seleccionada: ${selectedActivity.activity_type}`,
          `Ejecuta ${selectedActivity.activity_type}: ${selectedActivity.label}.`,
          tests.length ? `Pruebas solicitadas: ${tests.join(", ")}.` : null,
        ]
          .filter(Boolean)
          .join(" ")
      : originalPrompt;

    return [
      basePrompt,
      originalPrompt ? `Petición literal del usuario: ${originalPrompt}` : null,
      datasets.length ? `Datasets documentales detectados: ${datasets.join("; ")}.` : null,
      rules.length ? `Reglas documentales DC: ${rules.slice(0, 8).join(" | ")}.` : null,
      metrics.length ? `Métricas/valores documentales detectados: ${metrics.join(", ")}.` : null,
      "Ejecuta exclusivamente las pruebas de la actividad seleccionada y aplica los valores/reglas del DC cuando estén informados.",
    ]
      .filter(Boolean)
      .join(" ");
  };

  const buildCycleMetadataFromConceptualActivity = (activity) => {
    if (!activity) return null;

    const label = activity.label || activity.activity_type;

    return {
      project_label: activity.activity_type,
      review_label: `Ciclo DC - ${label}`,
      test_phase: label,
    };
  };

  const getMetadataFromExplicitActivityPrompt = (prompt) => {
    const text = (prompt || "").toLowerCase();

    const catalog = [
      {
        key: "minable_dataset_validation",
        project_label: "MINABLE_DATASET_VALIDATION",
        review_label: "Validación de tabla minable",
        test_phase: "Tabla minable",
      },
      {
        key: "dataset_split_validation",
        project_label: "DATASET_SPLIT_VALIDATION",
        review_label: "Validación de particiones train/validation/test",
        test_phase: "Particiones train/validation/test",
      },
      {
        key: "model_performance_evaluation",
        project_label: "MODEL_PERFORMANCE_EVALUATION",
        review_label: "Evaluación de desempeño del modelo",
        test_phase: "Desempeño del modelo",
      },
      {
        key: "threshold_quality_evaluation",
        project_label: "THRESHOLD_QUALITY_EVALUATION",
        review_label: "Evaluación de scores y umbrales",
        test_phase: "Scores y umbrales",
      },
    ];

    const matched = catalog.find((item) =>
      text.includes(`activity_type=${item.key}`) ||
      text.includes(`actividad seleccionada: ${item.key}`) ||
      text.includes(item.project_label.toLowerCase())
    );

    return matched
      ? {
          project_label: matched.project_label,
          review_label: matched.review_label,
          test_phase: matched.test_phase,
        }
      : null;
  };

  const ensureCycleMetadataForExecution = async (currentSessionId, cleanPrompt, fileToUse) => {
    const activeSession = getActiveSession(currentSessionId);

    if (activeSession?.project_label && activeSession?.review_label) {
      return true;
    }

    // 1) Prioridad DC: si el usuario eligió una actividad documental, no se infiere otra.
    const conceptualActivity = matchConceptualActivityFromPrompt(cleanPrompt);
    const conceptualMetadata = buildCycleMetadataFromConceptualActivity(conceptualActivity);
    if (conceptualMetadata) {
      await updateCycleMetadata(conceptualMetadata);
      return true;
    }

    // 2) Directiva explícita de activity_type generada por el modo documental.
    const explicitActivityMetadata = getMetadataFromExplicitActivityPrompt(cleanPrompt);
    if (explicitActivityMetadata) {
      await updateCycleMetadata(explicitActivityMetadata);
      return true;
    }

    // 3) Comportamiento original: inferencia por nombre/cabeceras del dataset.
    if (fileToUse) {
      const inferredContext = await inferDatasetExecutionContext(fileToUse);
      if (inferredContext?.metadata) {
        await updateCycleMetadata(inferredContext.metadata);
        return true;
      }
    }

    // 4) Último fallback legacy: inferencia por texto de revisión.
    const detectedPhase = inferTestPhaseFromPrompt(cleanPrompt);
    if (detectedPhase && detectedPhase !== "Fase no determinada") {
      await updateCycleMetadata({
        project_label: detectedPhase.toUpperCase().replace(/[^A-Z0-9]+/g, "_"),
        review_label: cleanPrompt.slice(0, 80) || detectedPhase,
        test_phase: detectedPhase,
      });
      return true;
    }

    return false;
  };

  const normalizeActivityText = (value) =>
    (value || "")
      .toString()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();

  const matchConceptualActivityFromPrompt = (prompt) => {
    if (!conceptualAnalysis?.supported_activities?.length) return null;

    const text = normalizeActivityText(prompt);

    const aliases = {
      MINABLE_DATASET_VALIDATION: [
        "validacion de tabla minable",
        "tabla minable",
        "calidad de tabla minable",
        "validar tabla minable",
        "validacion calidad dataset",
        "calidad dataset",
        "nulos duplicados data types outliers balance skewness",
        "nulls duplicates data types outliers balance skewness",
      ],
      MODEL_PERFORMANCE_EVALUATION: [
        "evaluacion de desempeno del modelo",
        "desempeno del modelo",
        "rendimiento del modelo",
        "performance del modelo",
        "accuracy precision recall f1 auc",
      ],
      DATASET_SPLIT_VALIDATION: [
        "validacion de particiones train validation test",
        "particiones train validation test",
        "dataset split",
        "split validation",
        "train validation test",
      ],
      THRESHOLD_QUALITY_EVALUATION: [
        "evaluacion de scores y umbrales",
        "scores y umbrales",
        "umbral",
        "threshold",
        "punto de corte",
      ],
    };

    const scored = conceptualAnalysis.supported_activities.map((activity) => {
      const activityTypeRaw = activity.activity_type || "";
      const activityType = normalizeActivityText(activityTypeRaw);
      const label = normalizeActivityText(activity.label);
      const tests = activity.tests || [];
      let score = 0;

      if (activityType && text.includes(activityType)) score += 120;
      if (label && text.includes(label)) score += 100;

      const activityAliases = aliases[activityTypeRaw] || [];
      activityAliases.forEach((alias) => {
        const normalizedAlias = normalizeActivityText(alias);
        if (normalizedAlias && text.includes(normalizedAlias)) score += 90;
      });

      if (activityTypeRaw === "MINABLE_DATASET_VALIDATION") {
        ["minable", "nulos", "nulls", "duplicados", "duplicates", "outliers", "tipos", "data types", "balance", "skewness"].forEach((word) => {
          if (text.includes(normalizeActivityText(word))) score += 12;
        });
      }

      if (activityTypeRaw === "MODEL_PERFORMANCE_EVALUATION") {
        ["modelo", "desempeno", "performance", "accuracy", "precision", "recall", "f1", "auc"].forEach((word) => {
          if (text.includes(normalizeActivityText(word))) score += 16;
        });
      }

      if (activityTypeRaw === "DATASET_SPLIT_VALIDATION") {
        ["split", "particion", "particiones", "train", "validation", "test", "conjunto"].forEach((word) => {
          if (text.includes(normalizeActivityText(word))) score += 16;
        });
      }

      if (activityTypeRaw === "THRESHOLD_QUALITY_EVALUATION") {
        ["umbral", "threshold", "punto de corte", "score"].forEach((word) => {
          if (text.includes(normalizeActivityText(word))) score += 16;
        });
      }

      tests.forEach((testName) => {
        const test = normalizeActivityText(testName);
        if (test && text.includes(test)) score += 18;
      });

      return { activity, score };
    });

    scored.sort((a, b) => b.score - a.score);

    return scored[0]?.score > 0 ? scored[0].activity : null;
  };



  const readCsvHeader = async (file) => {
    if (!file || !file.name?.toLowerCase().endsWith(".csv")) return [];

    try {
      const text = await file.slice(0, 4096).text();
      const firstLine = text.split(/\r?\n/).find((line) => line.trim());
      if (!firstLine) return [];

      return firstLine
        .split(",")
        .map((column) => column.trim().replace(/^"|"$/g, ""))
        .filter(Boolean);
    } catch (error) {
      console.warn("No se pudo leer la cabecera del dataset", error);
      return [];
    }
  };

  const inferDatasetExecutionContext = async (file) => {
    const fileName = (file?.name || "").toLowerCase();
    const columns = await readCsvHeader(file);
    const lowerColumns = columns.map((column) => column.toLowerCase());

    const hasColumn = (...names) =>
      lowerColumns.some((column) => names.some((name) => column === name || column.includes(name)));

    const targetColumn =
      columns.find((column) => ["abandono", "target", "y_true", "real", "label", "clase"].includes(column.toLowerCase())) ||
      columns.find((column) => ["target", "label", "clase", "real"].some((name) => column.toLowerCase().includes(name)));

    const scoreColumn =
      columns.find((column) => ["probabilidad_abandono", "score", "prediction", "prediccion", "predicción", "y_pred", "probabilidad"].includes(column.toLowerCase())) ||
      columns.find((column) => ["probabilidad", "score", "pred", "prediction"].some((name) => column.toLowerCase().includes(name)));

    const splitColumn =
      columns.find((column) => ["conjunto", "split", "partition", "particion", "partición", "subset"].includes(column.toLowerCase())) ||
      columns.find((column) => ["split", "conjunto", "partition", "particion", "subset"].some((name) => column.toLowerCase().includes(name)));

    const idColumn =
      columns.find((column) => ["cliente_id", "id", "customer_id", "row_id"].includes(column.toLowerCase())) ||
      columns.find((column) => column.toLowerCase().endsWith("_id"));

    if (fileName.includes("model_performance") || (targetColumn && scoreColumn)) {
      return {
        prompt: [
          "Evalúa el desempeño del modelo",
          targetColumn ? `target es ${targetColumn}` : null,
          scoreColumn ? `score es ${scoreColumn}` : null,
          idColumn ? `id es ${idColumn}` : null,
        ]
          .filter(Boolean)
          .join(" "),
        metadata: {
          project_label: "MODEL_PERFORMANCE_EVALUATION",
          review_label: "Evaluación de desempeño del modelo",
          test_phase: "Desempeño del modelo",
        },
      };
    }

    if (fileName.includes("split") || splitColumn || hasColumn("train", "validation", "test")) {
      return {
        prompt: [
          "Valida las particiones train/validation/test del dataset",
          splitColumn ? `split es ${splitColumn}` : null,
          targetColumn ? `target es ${targetColumn}` : null,
          idColumn ? `id es ${idColumn}` : null,
        ]
          .filter(Boolean)
          .join(" "),
        metadata: {
          project_label: "DATASET_SPLIT_VALIDATION",
          review_label: "Validación de particiones train/validation/test",
          test_phase: "Particiones train/validation/test",
        },
      };
    }

    return {
      prompt: [
        "Valida la calidad de tabla minable del dataset",
        targetColumn ? `target es ${targetColumn}` : null,
        idColumn ? `id es ${idColumn}` : null,
      ]
        .filter(Boolean)
        .join(" "),
      metadata: {
        project_label: "MINABLE_DATASET_VALIDATION",
        review_label: "Validación de tabla minable",
        test_phase: "Tabla minable",
      },
    };
  };
  const runAssessment = async ({
    promptToRun,
    fileToUse,
    autoTriggered = false,
    reason = null,
  }) => {
    const cleanPrompt = (promptToRun || "").trim();

    if (!cleanPrompt) return;

    try {
        const formData = new FormData();
        formData.append("user_message", cleanPrompt);
        if (USER_ID) formData.append("user_id", USER_ID);

        const validationResponse = await fetch(`${API_BASE}/chat`, {
          method: "POST",
          body: formData,
        });

        if (validationResponse.ok) {
          const data = await validationResponse.json();

          if (data.assistant_message?.includes("No he entendido") || 
              data.intent === "unknown") {
            await addAssistantMessageProgressively(data.assistant_message);
            return;
          }
        }
      } catch (error) {
        console.warn("Error validando intent:", error);
      }

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

      await fetch(`${API_BASE}/sessions/state`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          user_id: USER_ID,
          active_review_prompt: cleanPrompt,
          pending_prompt: cleanPrompt,
          last_processed_file_name: lastProcessedFileName,
        }),
      });

      await fetch(`${API_BASE}/sessions/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          user_id: USER_ID,
          role: "user",
          content: cleanPrompt,
          timestamp: timestamp(),
        }),
      });

      await fetch(`${API_BASE}/sessions/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          user_id: USER_ID,
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

      // Caso 2: hay artefacto. Antes de bloquear, restauramos el comportamiento original:
      // si el dataset o la petición permiten identificar la actividad/fase, autocompletamos
      // proyecto/ciclo/fase y ejecutamos. El modo DC solo tiene prioridad cuando existe
      // una actividad documental elegida explícitamente.
      const hasExecutableMetadata = await ensureCycleMetadataForExecution(
        currentSessionId,
        cleanPrompt,
        fileToUse
      );

      if (!hasExecutableMetadata) {
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
      formData.append("user_id", USER_ID);
      formData.append("file", fileToUse);

      if (conceptualAnalysis) {
        const matchedActivity = matchConceptualActivityFromPrompt(cleanPrompt);
        formData.append(
          "conceptual_analysis",
          JSON.stringify({
            ...conceptualAnalysis,
            selected_activity: matchedActivity || null,
          })
        );
      }

      await addProgressMessages();

      const response = await fetch(`${API_BASE}/chat`, {
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

    const conceptualActivity = matchConceptualActivityFromPrompt(promptToRun);

    if (conceptualActivity && !selectedFile) {
      const conceptualPrompt = buildPromptFromConceptualActivity(
        conceptualActivity.activity_type,
        promptToRun
      );

      addMessage("user", promptToRun);
      setInput("");

      const metadata = buildCycleMetadataFromConceptualActivity(conceptualActivity);
      if (metadata) {
        await updateCycleMetadata(metadata);
      }

      await runAssessment({
        promptToRun: conceptualPrompt,
        fileToUse: null,
        autoTriggered: false,
      });

      return;
    }

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

    let promptForExecution = promptToRun || activeReviewPrompt || "Analiza este dataset";

    // Comportamiento legacy protegido: si el usuario entrega solo dataset,
    // inferimos actividad/fase desde nombre y columnas antes de ejecutar.
    if (!promptToRun && selectedFile && !activeReviewPrompt) {
      const inferredContext = await inferDatasetExecutionContext(selectedFile);
      promptForExecution = inferredContext.prompt;
      if (inferredContext.metadata) {
        await updateCycleMetadata(inferredContext.metadata);
      }
    }

    await runAssessment({
      promptToRun: promptForExecution,
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
      return;
    }

    // Caso 3: comportamiento original de ayuda por columnas/nombre del dataset.
    // No ejecuta todavía; solo prepara fase/proyecto/ciclo para que el usuario pueda revisar.
    const inferredContext = await inferDatasetExecutionContext(file);
    if (inferredContext?.metadata) {
      await updateCycleMetadata(inferredContext.metadata);
    }
  };

  const handleConceptualDocumentUploaded = async (file) => {
    if (!file || isLoading) return;

    try {
      const currentSessionId = await ensureServerSession();
      setIsLoading(true);
      setDownloadEnabled(false);
      setConceptualAnalysis(null);

      const userContent = `He subido el documento de especificación ${file.name}`;
      const receivedContent = `He recibido el documento de especificación <b>${file.name}</b>. Voy a revisarlo para detectar actividades, reglas de negocio, datasets, modelos, dashboards, métricas y pruebas asociadas.`;

      addMessage("user", userContent);
      addMessage("assistant", receivedContent);

      const conceptualSteps = [
        "Pensando... interpretando documento conceptual...",
        "Detectando entidades funcionales y reglas de negocio...",
        "Mapeando actividades al catálogo de reglas QA...",
        "Generando propuesta de validaciones y pruebas...",
      ];

      for (const step of conceptualSteps) {
        addMessage("assistant", `<span class="text-qa-muted">${step}</span>`);
        await new Promise((resolve) => setTimeout(resolve, 350));
      }

      const formData = new FormData();
      formData.append("file", file);
      formData.append("session_id", currentSessionId);
      formData.append("user_id", USER_ID);

      const response = await fetch(`${API_BASE}/conceptual-documents/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Error analizando el documento conceptual");
      }

      const data = await response.json();
      setConceptualAnalysis(data.analysis || null);

      await addAssistantMessageProgressively(data.assistant_message);

      await fetch(`${API_BASE}/sessions/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          user_id: USER_ID,
          role: "user",
          content: userContent,
          timestamp: timestamp(),
        }),
      });

      await loadAvailableSessions();
    } catch (error) {
      console.error("Error en análisis conceptual:", error);
      addMessage(
        "assistant",
        "No he podido analizar el documento conceptual. Revisa que sea un .docx, .ipynb, .txt o .md válido y que el backend esté arrancado."
      );
    } finally {
      setIsLoading(false);
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
    setConceptualAnalysis(null);
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
    setConceptualAnalysis(null);

    if (setSelectedFile) {
      setSelectedFile(null);
    }

    if (setDownloadEnabled) {
      setDownloadEnabled(false);
    }

    localStorage.removeItem(sessionStorageKey);
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

  const currentSession = availableSessions.find(
    (session) => session.session_id === sessionId
  );

  const deleteIteration = async (executionId) => {
    if (!executionId || !sessionId || !USER_ID) return;

    try {
      const response = await fetch(
        `${API_BASE}/sessions/${sessionId}/reports/${executionId}?user_id=${USER_ID}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        console.warn("No se pudo eliminar la iteración en el servidor.");
        return false;
      }

      return true;
    } catch (error) {
      console.error("Error eliminando iteración:", error);
      return false;
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
    handleConceptualDocumentUploaded,
    conceptualAnalysis,
    pendingPrompt,
    activeReviewPrompt,
    sessionId,
    restoreSession,
    availableSessions,
    loadAvailableSessions,
    updateCycleMetadata,
    inferTestPhaseFromPrompt,
    reportPhaseFeedback,
    deleteIteration,
    currentSession,
  };
}