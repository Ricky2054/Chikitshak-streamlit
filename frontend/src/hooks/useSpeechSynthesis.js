import { useCallback, useEffect, useRef, useState } from "react";
import { getSpeechCode } from "../constants/languages";

export function useSpeechSynthesis(langCode) {
  const [speaking, setSpeaking] = useState(false);
  const utteranceRef = useRef(null);

  const stop = useCallback(() => {
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }, []);

  const speak = useCallback(
    (text) => {
      if (!text?.trim() || !window.speechSynthesis) return;

      stop();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = getSpeechCode(langCode);
      utterance.rate = 0.95;
      utterance.pitch = 1;

      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(
        (v) =>
          v.lang.startsWith(langCode) &&
          (v.name.includes("Google") || v.name.includes("Microsoft"))
      );
      if (preferred) utterance.voice = preferred;

      utterance.onend = () => setSpeaking(false);
      utterance.onerror = () => setSpeaking(false);
      utteranceRef.current = utterance;
      setSpeaking(true);
      window.speechSynthesis.speak(utterance);
    },
    [langCode, stop]
  );

  useEffect(() => () => stop(), [stop]);

  return { speak, stop, speaking };
}
