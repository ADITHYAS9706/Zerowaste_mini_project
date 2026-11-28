
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import "./index.css";
import App from "./App";

function RootApp() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Open the manager dashboard directly */}
        <Route path="/" element={<App />} />

        {/* Temporarily bypass authentication */}
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="/register" element={<Navigate to="/" replace />} />

        {/* Dashboard shortcuts */}
        <Route path="/manager" element={<Navigate to="/" replace />} />
        <Route path="/staff" element={<Navigate to="/" replace />} />

        {/* Redirect unknown URLs */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <RootApp />
  </StrictMode>
);
