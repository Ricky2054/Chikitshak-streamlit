import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import en from "./locales/en.json";
import hi from "./locales/hi.json";
import ta from "./locales/ta.json";
import te from "./locales/te.json";
import mr from "./locales/mr.json";
import bn from "./locales/bn.json";
import es from "./locales/es.json";
import ar from "./locales/ar.json";
import fr from "./locales/fr.json";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      hi: { translation: hi },
      ta: { translation: ta },
      te: { translation: te },
      mr: { translation: mr },
      bn: { translation: bn },
      es: { translation: es },
      ar: { translation: ar },
      fr: { translation: fr },
    },
    fallbackLng: "en",
    supportedLngs: ["en", "hi", "ta", "te", "mr", "bn", "kn", "ml", "es", "ar", "fr"],
    interpolation: { escapeValue: false },
    detection: {
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
    },
  });

export default i18n;
