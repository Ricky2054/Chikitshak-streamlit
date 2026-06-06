import React from "react";
import { useTranslation } from "react-i18next";

export default function MedicationCards({ medications }) {
  const { t } = useTranslation();
  if (!medications?.length) return null;

  return (
    <section className="medication-panel">
      <header className="medication-panel__head">
        <h3>{t("results.medications")}</h3>
        <p className="muted">{t("results.medicationsSub")}</p>
      </header>
      <div className="medication-grid">
        {medications.map((med, i) => (
          <article key={`${med.generic_name}-${i}`} className="medication-card">
            <div className="medication-card__media">
              {med.image_url ? (
                <img
                  src={med.image_url}
                  alt={med.generic_name}
                  loading="lazy"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              ) : (
                <div className="medication-card__placeholder">{med.generic_name?.[0] || "?"}</div>
              )}
            </div>
            <div className="medication-card__body">
              <h4>{med.generic_name}</h4>
              {med.name !== med.generic_name && (
                <p className="medication-card__alias">{t("results.matchedAs")}: {med.name}</p>
              )}
              <p className="medication-card__dose medication-card__dose--primary">
                <strong>{t("results.dose")}:</strong>{" "}
                {med.display_dose || med.suggested_dose || med.protocol_dose || "—"}
              </p>
              {med.suggested_dose && med.suggested_dose !== (med.display_dose || med.protocol_dose) && (
                <p className="medication-card__suggested">
                  <strong>{t("results.weightDose")}:</strong> {med.suggested_dose}
                </p>
              )}
              {med.protocol_dose &&
                med.protocol_dose !== (med.display_dose || med.suggested_dose) &&
                med.protocol_dose !== "See institutional protocol" && (
                <p className="medication-card__protocol">
                  <strong>{t("results.protocolDose")}:</strong> {med.protocol_dose}
                </p>
              )}
              <p className="medication-card__note">{med.personalized_note}</p>
              {med.image_source && (
                <span className="medication-card__src">{med.image_source}</span>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
