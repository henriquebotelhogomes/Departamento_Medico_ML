import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Layout } from "@/components/Layout";
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import { Predict } from "@/pages/Predict";
import { History } from "@/pages/History";
import { Dashboard } from "@/pages/Dashboard";

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="/predict" element={<Predict />} />
              <Route path="/history" element={<History />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Route>
            <Route path="*" element={<Navigate to="/predict" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}
