/** BCP-47 speech codes for Web Speech API (Google engine in Chrome/Edge) */
export const LANGUAGES = [
  { code: "en", label: "English", speech: "en-US", flag: "🇺🇸" },
  { code: "hi", label: "हिन्दी", speech: "hi-IN", flag: "🇮🇳" },
  { code: "ta", label: "தமிழ்", speech: "ta-IN", flag: "🇮🇳" },
  { code: "te", label: "తెలుగు", speech: "te-IN", flag: "🇮🇳" },
  { code: "mr", label: "मराठी", speech: "mr-IN", flag: "🇮🇳" },
  { code: "bn", label: "বাংলা", speech: "bn-IN", flag: "🇮🇳" },
  { code: "kn", label: "ಕನ್ನಡ", speech: "kn-IN", flag: "🇮🇳" },
  { code: "ml", label: "മലയാളം", speech: "ml-IN", flag: "🇮🇳" },
  { code: "es", label: "Español", speech: "es-ES", flag: "🇪🇸" },
  { code: "ar", label: "العربية", speech: "ar-SA", flag: "🇸🇦" },
  { code: "fr", label: "Français", speech: "fr-FR", flag: "🇫🇷" },
];

export function getSpeechCode(langCode) {
  return LANGUAGES.find((l) => l.code === langCode)?.speech || "en-US";
}

export function isSpeechSupported() {
  return (
    typeof window !== "undefined" &&
    ("SpeechRecognition" in window || "webkitSpeechRecognition" in window)
  );
}

export function isSpeechSynthesisSupported() {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}
