import { Toaster } from "@/components/ui/toaster"
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClientInstance } from '@/lib/query-client'
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import PageNotFound from './lib/PageNotFound';
import { AuthProvider, useAuth } from '@/lib/AuthContext';
import UserNotRegisteredError from '@/components/UserNotRegisteredError';
import ScrollToTop from './components/ScrollToTop';

// Páginas de la aplicación
import Layout from "@/components/Layout";
import { RoleProvider } from "@/lib/RoleContext";
import Dashboard from "@/pages/Dashboard";
import Pacientes from "@/pages/Pacientes";
import PacienteDetalle from "@/pages/PacienteDetalle";
import Vacunacion from "@/pages/Vacunacion";
import Citas from "@/pages/Citas";
import Cartilla from "@/pages/Cartilla";
import Reportes from "@/pages/Reportes";
import Administracion from "@/pages/Administracion";

// Páginas de autenticación
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";

const AuthenticatedApp = () => {
  const { isLoadingAuth, isLoadingPublicSettings, authError, navigateToLogin } = useAuth();

  // Spinner sólo si está explícitamente cargando
  if (isLoadingPublicSettings || isLoadingAuth) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background">
        <div className="w-8 h-8 border-4 border-slate-200 border-t-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  // Manejo de errores de autenticación
  if (authError) {
    if (authError.type === 'user_not_registered') {
      return <UserNotRegisteredError />;
    } else if (authError.type === 'auth_required') {
      navigateToLogin();
      return null;
    }
  }

  return (
    <Routes>
      {/* Rutas principales del sistema SNCEV */}
      <Route element={<RoleProvider><Layout /></RoleProvider>}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/pacientes" element={<Pacientes />} />
        <Route path="/pacientes/:id" element={<PacienteDetalle />} />
        <Route path="/vacunacion" element={<Vacunacion />} />
        <Route path="/citas" element={<Citas />} />
        <Route path="/cartilla" element={<Cartilla />} />
        <Route path="/reportes" element={<Reportes />} />
        <Route path="/administracion" element={<Administracion />} />
      </Route>

      {/* Rutas públicas de autenticación */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      {/* Página 404 */}
      <Route path="*" element={<PageNotFound />} />
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClientInstance}>
        <Router>
          <ScrollToTop />
          <AuthenticatedApp />
        </Router>
        <Toaster />
      </QueryClientProvider>
    </AuthProvider>
  );
}

export default App;