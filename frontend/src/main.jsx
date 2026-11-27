
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import "./index.css";

import Login from "./pages/Login";
import Register from "./pages/Register";

function DashboardSetup() {
  return (
    <div style={{
      minHeight: "100vh",
      display: "grid",
      placeItems: "center",
      padding: "24px",
      fontFamily: "Arial, sans-serif",
      textAlign: "center",
    }}>
      <div>
        <h2>Authentication successful</h2>
        <p>Your dashboard integration is the next step.</p>
        <a href="/login">Return to login</a>
      </div>
    </div>
  );
}

function RootApp() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Temporary destinations until protected dashboards are connected */}
        <Route path="/manager" element={<DashboardSetup />} />
        <Route path="/staff" element={<DashboardSetup />} />

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <RootApp />
  </StrictMode>
);
