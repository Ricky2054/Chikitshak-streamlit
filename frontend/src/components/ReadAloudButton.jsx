import React from "react";
import { useTranslation } from "react-i18next";
import { useSpeechSynthesis } from "../hooks/useSpeechSynthesis";
import { IconSpeaker } from "./Icons";

export default function ReadAloudButton({ text, langCode }) {
  const { t } = useTranslation();
  const { speak, stop, speaking } = useSpeechSynthesis(langCode);

  if (!text?.trim()) return null;

  return (
    <button
      type="button"
      className={`read-aloud-btn ${speaking ? "is-active" : ""}`}
      onClick={() => (speaking ? stop() : speak(text))}
    >
      <IconSpeaker />
      {speaking ? t("voice.stopReading") : t("voice.readAloud")}
    </button>
  );
}
