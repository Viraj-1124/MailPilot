import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [userEmail, setUserEmail] = useState(null);
  const [loading, setLoading] = useState(true);

  // In a real app we might check localStorage or a session cookie here
  // For this stateless requirement, we start null. 
  // But to survive refresh for demo convenience we might want to store it temporarily if allowed.
  // The requirement says "no localStorage for now", so we stick to memory.
  // However, on refresh, the user will be logged out.

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = await api.getMe();
        if (user && user.email) {
          setUserEmail(user.email);
        }
      } catch (error) {
        console.log("Not logged in");
        setUserEmail(null);
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  const login = (email) => {
    // This might be used if we want to manually set state, 
    // but usually flow is via OAuth redirect.
    setUserEmail(email);
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (e) {
      console.error("Logout failed", e);
    }
    setUserEmail(null);
  };

  return (
    <AuthContext.Provider value={{ userEmail, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
