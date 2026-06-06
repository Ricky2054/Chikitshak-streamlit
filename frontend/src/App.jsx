import React from "react";
import { useTranslation } from "react-i18next";
import { AuthProvider, useAuth } from "./AuthContext";
import MedicalForm from "./MedicalForm";
import LanguageSelector from "./components/LanguageSelector";
import { LogoMark } from "./components/Icons";
import "./App.css";

function TopBar() {
  const { t } = useTranslation();
  const { user, login, logout, loading, authEnabled } = useAuth();

  return (
    <header className="topbar">
      <div className="topbar__brand">
        <LogoMark />
        <div>
          <strong className="topbar__title">MedRAG</strong>
          <span className="topbar__meta">{t("app.eyebrow")}</span>
        </div>
      </div>
      <div className="topbar__actions">
        <LanguageSelector />
        {authEnabled && (
          <div className="topbar__auth">
            {loading ? (
              <span className="muted">…</span>
            ) : user ? (
              <>
                <span className="topbar__user">{user.displayName || user.email}</span>
                <button type="button" className="btn-text" onClick={logout}>
                  Sign out
                </button>
              </>
            ) : (
              <button type="button" className="btn-text" onClick={login}>
                Sign in
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

function App() {
  const { t, i18n } = useTranslation();
  const isRtl = i18n.language === "ar";

  return (
    <AuthProvider>
      <div className="app" dir={isRtl ? "rtl" : "ltr"}>
        <TopBar />
        <main className="main">
          <MedicalForm />
        </main>
        <footer className="footer">
          <span>{t("app.footer")}</span>
        </footer>
      </div>
    </AuthProvider>
  );
}

export default App;
