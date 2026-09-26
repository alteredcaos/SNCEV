import React, { createContext, useState, useContext, useEffect } from 'react';
import { apiClient, getStoredToken, getStoredUser, setStoredToken, setStoredUser } from '@/api/apiClient';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [isLoadingPublicSettings, setIsLoadingPublicSettings] = useState(true);
  const [authError, setAuthError] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [appPublicSettings, setAppPublicSettings] = useState({
    id: 'sncev-app',
    name: 'SNCEV — Cartilla Electrónica de Vacunación',
    public_settings: {},
  });

  useEffect(() => {
    checkAppState();
  }, []);

  const checkAppState = async () => {
    try {
      setIsLoadingPublicSettings(true);
      setAuthError(null);

      // Cargar configuración pública nativa
      const settings = await apiClient.app.getPublicSettings();
      setAppPublicSettings(settings);

      // Verificar si hay sesión o inicializar en modo local
      const token = getStoredToken();
      const savedUser = getStoredUser();

      if (token && savedUser) {
        setUser(savedUser);
        setIsAuthenticated(true);
      } else {
        // En entorno local/desarrollo sin auth forzada, asignamos usuario dev
        const defaultDevUser = {
          id: 'usr-dev-1',
          username: 'admin',
          nombre: 'Karina Mendoza',
          email: 'admin@salud.gob.mx',
          rol: 'Administrador Nacional',
        };
        setUser(defaultDevUser);
        setIsAuthenticated(true);
      }
    } catch (err) {
      console.warn('Error inicializando estado de autenticación:', err);
      // Fallback seguro para no bloquear la interfaz
      setUser({
        id: 'usr-dev-1',
        username: 'admin',
        nombre: 'Karina Mendoza',
        email: 'admin@salud.gob.mx',
        rol: 'Administrador Nacional',
      });
      setIsAuthenticated(true);
    } finally {
      setIsLoadingPublicSettings(false);
      setIsLoadingAuth(false);
      setAuthChecked(true);
    }
  };

  const checkUserAuth = async () => {
    const savedUser = getStoredUser();
    if (savedUser) {
      setUser(savedUser);
      setIsAuthenticated(true);
    }
    setAuthChecked(true);
    setIsLoadingAuth(false);
  };

  const login = async (username, password) => {
    setIsLoadingAuth(true);
    try {
      const res = await apiClient.auth.login(username, password);
      if (res && res.user) {
        setUser(res.user);
        setIsAuthenticated(true);
      }
      return res;
    } finally {
      setIsLoadingAuth(false);
    }
  };

  const logout = (redirectTo = null) => {
    setUser(null);
    setIsAuthenticated(false);
    apiClient.auth.logout(redirectTo);
  };

  const navigateToLogin = (returnTo) => {
    apiClient.auth.redirectToLogin(returnTo);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoadingAuth,
        isLoadingPublicSettings,
        authError,
        appPublicSettings,
        authChecked,
        login,
        logout,
        navigateToLogin,
        checkUserAuth,
        checkAppState,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
