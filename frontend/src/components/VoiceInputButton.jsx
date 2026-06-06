import React from "react";
import { useTranslation } from "react-i18next";
import { getSpeechCode, isSpeechSupported } from "../constants/languages";
import { useVoiceRecognition } from "../hooks/useVoiceRecognition";
import { IconMic, IconStop } from "./Icons";

export default function VoiceInputButton({ onTranscript, disabled, baseText = "" }) {
  const { t, i18n } = useTranslation();
  const speechLang = getSpeechCode(i18n.language?.split("-")[0] || "en");
  const browserOk = isSpeechSupported();

  const handleTranscript = React.useCallback(
    (text) => onTranscript(text.trimEnd()),
    [onTranscript]
  );

  const { listening, start, stop, supported } = useVoiceRecognition({
    language: speechLang,
    onTranscript: handleTranscript,
    disabled,
  });

  if (!browserOk || !supported) {
    return (
      <span className="voice-fallback" title={t("voice.unsupported")}>
        <IconMic />
      </span>
    );
  }

  const handleClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (listening) {
      stop();
    } else {
      start(baseText);
    }
  };

  return (
    <div className={`voice-control ${listening ? "is-active" : ""}`}>
      <button
        type="button"
        className="voice-btn"
        onClick={handleClick}
        disabled={disabled}
        aria-pressed={listening}
        aria-label={listening ? t("voice.stop") : t("voice.start")}
      >
        {listening ? <IconStop /> : <IconMic />}
        <span>{listening ? t("voice.stop") : t("voice.start")}</span>
      </button>
      {listening && (
        <span className="voice-wave" aria-live="polite">
          <span /><span /><span /><span />
          {t("voice.listen")}
        </span>
      )}
    </div>
  );
}
