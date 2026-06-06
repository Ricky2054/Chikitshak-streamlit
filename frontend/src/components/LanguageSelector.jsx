import React from "react";
import { useTranslation } from "react-i18next";
import { LANGUAGES } from "../constants/languages";
import { IconGlobe } from "./Icons";

export default function LanguageSelector() {
  const { i18n, t } = useTranslation();
  const current = i18n.language?.split("-")[0] || "en";

  return (
    <div className="lang-selector">
      <IconGlobe aria-hidden="true" />
      <select
        id="lang-select"
        className="lang-select"
        value={current}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
        aria-label={t("lang.label")}
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.label}
          </option>
        ))}
      </select>
    </div>
  );
}
