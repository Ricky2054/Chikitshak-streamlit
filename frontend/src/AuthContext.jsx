import React, { createContext, useContext, useEffect, useState } from "react";
import { auth, provider, authEnabled } from "./firebase";
import { signInWithPopup, signOut, onAuthStateChanged } from "firebase/auth";

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(authEnabled);
  const [idToken, setIdToken] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || "";

  useEffect(() => {
    if (!authEnabled) {
      setLoading(false);
      return undefined;
    }

    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        firebaseUser
          .getIdToken()
          .then((token) => setIdToken(token))
          .catch(() => setIdToken(null))
          .finally(() => setLoading(false));
      } else {
        setIdToken(null);
        setLoading(false);
      }
    });
    return () => unsubscribe();
  }, []);

  const verifyWithBackend = async (token) => {
    const res = await fetch(`${API_URL}/api/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_token: token }),
    });
    if (!res.ok) throw new Error("Backend verification failed");
    return await res.json();
  };

  const login = async () => {
    if (!authEnabled) return;
    const result = await signInWithPopup(auth, provider);
    const token = await result.user.getIdToken();
    setIdToken(token);
    await verifyWithBackend(token);
  };

  const logout = async () => {
    if (!authEnabled) return;
    await signOut(auth);
    setIdToken(null);
  };

  const getProfile = async () => {
    if (!idToken) throw new Error("No ID token available");
    const res = await fetch(`${API_URL}/api/profile`, {
      headers: { Authorization: `Bearer ${idToken}` },
    });
    if (!res.ok) throw new Error("Failed to fetch profile");
    return await res.json();
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, idToken, getProfile, authEnabled }}>
      {children}
    </AuthContext.Provider>
  );
};
