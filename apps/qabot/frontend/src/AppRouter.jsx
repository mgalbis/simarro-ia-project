import React, { useState } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import Login from "./components/Login.jsx";
import App from "./App.jsx";

export default function AppRouter() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("qabot_user");
    return saved ? JSON.parse(saved) : null;
  });

  const navigate = useNavigate();

  const handleLoginSuccess = (userData) => {
    localStorage.setItem("qabot_user", JSON.stringify(userData));
    setUser(userData);
    navigate("/chat");
  };

  const handleLogout = () => {
    localStorage.removeItem("qabot_user");
    setUser(null);
    navigate("/login");
  };

  return (
    <Routes>
      <Route
        path="/login"
        element={
          user
            ? <Navigate to="/chat" replace />
            : <Login onLoginSuccess={handleLoginSuccess} />
        }
      />
      <Route
        path="/chat"
        element={
          user
            ? <App user={user} onLogout={handleLogout} />
            : <Navigate to="/login" replace />
        }
      />
      <Route
        path="*"
        element={<Navigate to={user ? "/chat" : "/login"} replace />}
      />
    </Routes>
  );
}