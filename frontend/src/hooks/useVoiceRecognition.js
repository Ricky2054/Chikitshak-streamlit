import { useCallback, useEffect, useRef, useState } from "react";

function getSpeechRecognition() {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

/**
 * Native Web Speech API hook with reliable manual stop (all languages).
 * Avoids react-speech-recognition stop bugs in continuous mode.
 */
export function useVoiceRecognition({ language, onTranscript, disabled }) {
  const recognitionRef = useRef(null);
  const manualStopRef = useRef(true);
  const baseTextRef = useRef("");
  const sessionTextRef = useRef("");
  const [listening, setListening] = useState(false);
  const [supported] = useState(() => !!getSpeechRecognition());

  const teardown = useCallback(() => {
    const rec = recognitionRef.current;
    if (!rec) return;
    recognitionRef.current = null;
    rec.onresult = null;
    rec.onend = null;
    rec.onerror = null;
    try {
      rec.abort();
    } catch {
      try {
        rec.stop();
      } catch {
        /* ignore */
      }
    }
  }, []);

  const stop = useCallback(() => {
    manualStopRef.current = true;
    teardown();
    setListening(false);
  }, [teardown]);

  const start = useCallback(
    (baseText = "") => {
      if (disabled) return;
      const SR = getSpeechRecognition();
      if (!SR) return;

      stop();
      manualStopRef.current = false;
      baseTextRef.current = baseText;
      sessionTextRef.current = "";

      const rec = new SR();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = language;
      rec.maxAlternatives = 1;

      rec.onresult = (event) => {
        let interim = "";
        let finalChunk = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          const piece = event.results[i][0]?.transcript || "";
          if (event.results[i].isFinal) finalChunk += piece;
          else interim += piece;
        }
        if (finalChunk) sessionTextRef.current += finalChunk;
        const combined = `${baseTextRef.current}${sessionTextRef.current}${interim}`.trim();
        onTranscript(combined ? `${combined} ` : "");
      };

      rec.onerror = (event) => {
        if (event.error === "aborted" || event.error === "no-speech") return;
        manualStopRef.current = true;
        teardown();
        setListening(false);
      };

      rec.onend = () => {
        if (manualStopRef.current || recognitionRef.current !== rec) {
          setListening(false);
          return;
        }
        try {
          rec.start();
        } catch {
          setListening(false);
        }
      };

      recognitionRef.current = rec;
      try {
        rec.start();
        setListening(true);
      } catch {
        manualStopRef.current = true;
        setListening(false);
      }
    },
    [disabled, language, onTranscript, stop, teardown]
  );

  useEffect(() => {
    if (disabled && listening) stop();
  }, [disabled, listening, stop]);

  useEffect(() => {
    if (listening) stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  useEffect(() => () => stop(), [stop]);

  return { listening, start, stop, supported };
}
