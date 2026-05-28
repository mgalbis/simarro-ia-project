import React, { useState } from "react";

export default function Login({ onLoginSuccess }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const resetForm = () => {
    setUsername("");
    setPassword("");
    setConfirmPassword("");
    setError("");
    setSuccess("");
  };

  const switchMode = (newMode) => {
    resetForm();
    setMode(newMode);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Por favor, rellena todos los campos.");
      return;
    }
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();

      if (data.ok) {
        onLoginSuccess({ id: data.id, username: data.username });
      } else {
        setError(data.error || "Credenciales incorrectas.");
      }
      } catch {
        setError("Error al conectar con el servidor.");
      } finally {
        setIsLoading(false);
      }
    };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim() || !confirmPassword.trim()) {
      setError("Por favor, rellena todos los campos.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres.");
      return;
    }
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch("http://localhost:8000/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();

      if (data.ok) {
        setSuccess("Cuenta creada correctamente. Iniciando sesión...");
        setTimeout(() => onLoginSuccess({ id: data.id, username: data.username }), 1500);
      } else {
        setError(data.error || "Error al crear la cuenta.");
      }
    } catch {
      setError("Error al conectar con el servidor.");
    } finally {
      setIsLoading(false);
    }
  };

  const isLogin = mode === "login";

  return (
    <div className="relative min-h-screen w-full bg-qa-deep overflow-hidden font-sans">
      {/* FONDO ORIGINAL CONSERVADO, CON EL ORDENADOR REDUCIDO */}
      <div
        className="absolute inset-0 z-0 bg-no-repeat"
        style={{
          backgroundImage: `url('/QABotLogin.png')`,
          backgroundSize: "78% auto",
          backgroundPosition: "center",
          top: "-15%",
        }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-r from-qa-deep/80 via-transparent to-qa-deep/80" />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-qa-deep/60 via-transparent to-qa-deep/80" />

      {/* CONTENEDOR CENTRADO */}
      <div className="relative z-10 flex min-h-screen items-center justify-left px-6 py-8 left-30">
        <div className="flex w-full max-w-[440px] flex-col items-left gap-7">
          <div className="rounded-2xl bg-[#BF00FF] px-8 py-3 text-left text-[13px] font-black uppercase tracking-[0.28em] text-white shadow-[0_0_28px_rgba(191,0,255,0.55)]">
            Oficina de test inteligente
          </div>

          {/* LOGO + TÍTULO */}
          <div className="flex items-center justify-center gap-4">
            <div className="w-[70px] h-[70px] rounded-3xl bg-qa-bot-gradient shadow-[0_0_20px_rgba(142,53,255,0.70)]">
              <img src="/QABotIcon.png" alt="QABot" className="w-full h-full object-contain scale-105" />
            </div>

            <div className="flex flex-col">
              <h1 className="text-5xl font-[900] leading-none tracking-wide">
                <span className="text-white">QA</span>
                <span className="text-qa-purple-light">Bot</span>
                <span className="text-white"> - </span>
                <span className="italic text-qa-purple-light">OTI</span>
              </h1>

              <p className="text-[11px] uppercase tracking-[0.25em] text-white/60 font-normal mt-1">
                Asistente agéntico de calidad
              </p>
            </div>
          </div>

          {/* FORMULARIO */}
          <form
            onSubmit={isLogin ? handleLogin : handleRegister}
            className="w-full bg-qa-panel/90 border-2 border-qa-purple/40 rounded-[22px] backdrop-blur-xl shadow-[0_0_40px_rgba(142,53,255,0.2)] p-8 flex flex-col gap-5"
          >
            {/* Header */}
            <div className="border-b border-qa-purple/20 pb-4">
              <div className="flex items-center gap-2">
                <span className="text-qa-purple-light text-lg">◈</span>
                <h3 className="text-lg font-black text-white">
                  {isLogin ? "Ingreso de Usuario" : "Crear Cuenta"}
                </h3>
              </div>
              <p className="text-[11px] text-qa-muted mt-1">
                {isLogin
                  ? "Accede con tus credenciales para continuar"
                  : "Rellena los campos para registrarte"}
              </p>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-900/20 border border-red-500/40 text-red-400 text-xs p-3 rounded-xl italic">
                ⚠️ {error}
              </div>
            )}

            {/* Éxito */}
            {success && (
              <div className="bg-green-900/20 border border-green-500/40 text-green-400 text-xs p-3 rounded-xl italic">
                ✓ {success}
              </div>
            )}

            {/* Usuario */}
            <div className="flex flex-col gap-2">
              <label className="text-[10px] font-black uppercase tracking-wider text-qa-purple-light">
                Usuario
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="ej. admin"
                className="w-full bg-black/40 border-2 border-qa-purple/20 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-qa-purple/60 transition-all placeholder:text-gray-500 shadow-inner"
              />
            </div>

            {/* Contraseña */}
            <div className="flex flex-col gap-2">
              <label className="text-[10px] font-black uppercase tracking-wider text-qa-purple-light">
                Contraseña
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-black/40 border-2 border-qa-purple/20 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-qa-purple/60 transition-all placeholder:text-gray-500 shadow-inner"
              />
            </div>

            {/* Confirmar contraseña */}
            {!isLogin && (
              <div className="flex flex-col gap-2">
                <label className="text-[10px] font-black uppercase tracking-wider text-qa-purple-light">
                  Confirmar Contraseña
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-black/40 border-2 border-qa-purple/20 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-qa-purple/60 transition-all placeholder:text-gray-500 shadow-inner"
                />
              </div>
            )}

            {/* Botón principal */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-1 bg-gradient-to-r from-qa-purple to-[#5b13db] py-3.5 rounded-xl text-xs font-black uppercase tracking-widest text-white shadow-[0_0_20px_rgba(142,53,255,0.4)] hover:brightness-110 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading
                ? (isLogin ? "Autenticando..." : "Creando cuenta...")
                : (isLogin ? "Iniciar Sesión" : "Crear Cuenta")}
            </button>

            {/* Switch de modo */}
            <div className="text-center text-[11px] pt-1 border-t border-qa-purple/10">
              {isLogin ? (
                <span className="text-qa-muted">
                  ¿No tienes cuenta?{" "}
                  <button
                    type="button"
                    onClick={() => switchMode("register")}
                    className="text-qa-purple-light font-black hover:underline transition-all"
                  >
                    Regístrate aquí
                  </button>
                </span>
              ) : (
                <span className="text-qa-muted">
                  ¿Ya tienes sesión?{" "}
                  <button
                    type="button"
                    onClick={() => switchMode("login")}
                    className="text-qa-purple-light font-black hover:underline transition-all"
                  >
                    Inicia sesión
                  </button>
                </span>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}