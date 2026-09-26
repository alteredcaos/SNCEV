import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LogIn, User, Lock, Loader2, ShieldCheck } from "lucide-react";
import AuthLayout from "@/components/AuthLayout";
import { safeReturnTo } from "@/lib/authReturnTo";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const returnTo = safeReturnTo();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate(returnTo === "/login" ? "/" : returnTo);
    } catch (err) {
      setError(err.message || "Usuario o contraseña incorrectos");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError("");
    setLoading(true);
    try {
      await login("admin", "Admin123456!#");
      navigate("/");
    } catch (err) {
      setError(err.message || "Error al iniciar sesión demo");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      icon={LogIn}
      title="SNCEV — Iniciar Sesión"
      subtitle="Sistema Nacional de Cartilla Electrónica de Vacunación"
      footer={
        <div className="text-center text-xs text-muted-foreground space-y-1">
          <p>Acceso restringido para personal de salud autorizado.</p>
        </div>
      }
    >
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="username">Usuario o Correo Institucional</Label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" aria-hidden="true" />
            <Input
              id="username"
              type="text"
              autoComplete="username"
              autoFocus
              placeholder="admin o tu.nombre@salud.gob.mx"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="pl-10 h-12"
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Contraseña</Label>
            <Link to="/forgot-password" className="text-xs text-primary hover:underline">
              ¿Olvidaste tu contraseña?
            </Link>
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" aria-hidden="true" />
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="pl-10 h-12"
              required
            />
          </div>
        </div>

        <Button type="submit" className="w-full h-12 font-medium" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Iniciando sesión...
            </>
          ) : (
            "Iniciar Sesión"
          )}
        </Button>

        <div className="pt-2">
          <Button
            type="button"
            variant="outline"
            className="w-full h-10 text-xs text-muted-foreground hover:text-foreground"
            onClick={handleDemoLogin}
          >
            <ShieldCheck className="w-4 h-4 mr-1.5 text-primary" />
            Acceso Rápido / Modo Local (Admin)
          </Button>
        </div>
      </form>
    </AuthLayout>
  );
}
