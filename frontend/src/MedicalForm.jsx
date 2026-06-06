import React, { useRef, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "./AuthContext";
import { analyzeMedicalCase } from "./useMedicalAnalysis";
import { parseAnalysis } from "./utils/parseAnalysis";
import VoiceInputButton from "./components/VoiceInputButton";
import ReadAloudButton from "./components/ReadAloudButton";
import MedicationCards from "./components/MedicationCards";
import {
  IconSymptoms,
  IconPrescription,
  IconLab,
  IconUpload,
  IconShield,
  IconDoc,
  IconAlert,
  IconCheck,
  IconArrow,
} from "./components/Icons";

const INPUT_TYPE_IDS = ["Symptoms", "Prescription Review", "Test Results"];

const EXAMPLE_QUERIES = [
  {
    type: "Symptoms",
    labelKey: "examples.symptoms1",
    text: "A 35-year-old has fever, sore throat, and difficulty swallowing for 2 days. What are common causes and when should they seek urgent care?",
  },
  {
    type: "Symptoms",
    labelKey: "examples.symptoms2",
    text: "Patient presents with chest pain radiating to the left arm. What are initial assessment considerations in the emergency setting?",
  },
  {
    type: "Test Results",
    labelKey: "examples.tests1",
    text: "Low hemoglobin on CBC — what are common causes and what follow-up might a clinician consider?",
  },
  {
    type: "Prescription Review",
    labelKey: "examples.prescription1",
    text: "Tab. Metformin(500) BDPC. Tab Azithromycin 500 od x 5 days. Cap Pantop 40 mg od before breakfast. Please review for interactions and protocol alignment.",
  },
];

function Pipeline({ step }) {
  const { t } = useTranslation();
  const steps = [
    { label: t("loading.safety"), Icon: IconShield },
    { label: t("loading.doctor"), Icon: IconDoc },
    { label: t("loading.supervisor"), Icon: IconCheck },
  ];

  return (
    <div className="pipeline">
      <div className="pipeline__spinner" />
      <h3 className="pipeline__title">{t("loading.title")}</h3>
      <p className="pipeline__sub">{t("loading.subtitle")}</p>
      <ol className="pipeline__steps">
        {steps.map(({ label, Icon }, i) => (
          <li
            key={label}
            className={`pipeline__step ${i <= step ? "done" : ""} ${i === step ? "current" : ""}`}
          >
            <span className="pipeline__dot"><Icon /></span>
            {label}
          </li>
        ))}
      </ol>
    </div>
  );
}

function ResultBlock({ title, variant, children, icon: Icon }) {
  return (
    <section className={`result-block result-block--${variant}`}>
      <header className="result-block__head">
        {Icon && <Icon />}
        <h3>{title}</h3>
      </header>
      <div className="result-block__body">{children}</div>
    </section>
  );
}

function ResultView({ data, langCode }) {
  const { t } = useTranslation();
  const result = data?.result || {};
  const analysis = result.analysis || "";
  const medications = result.medications || [];
  const finalPlan = result.final_plan || {};
  const blocked = result.status === "blocked";
  const error = result.status === "error";
  const parsed = parseAnalysis(analysis);

  const fullText = [
    parsed.summary,
    ...parsed.guidance,
    ...parsed.redFlags,
    finalPlan.treatment,
    ...(finalPlan.additional_tests || []),
  ]
    .filter(Boolean)
    .join(". ");

  if (blocked || error) {
    return (
      <div className="result-alert">
        <IconAlert />
        <div>
          <h3>{blocked ? t("results.blocked") : t("results.error")}</h3>
          <p>{result.message || "Please try rephrasing your question."}</p>
          {blocked && <p className="muted">{t("results.blockedHint")}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="results-doc">
      <div className="results-doc__toolbar">
        <span className="status-pill">{t("results.complete")}</span>
        <ReadAloudButton text={fullText} langCode={langCode} />
      </div>

      {parsed.summary && (
        <ResultBlock title={t("results.summary")} variant="summary" icon={IconDoc}>
          <p>{parsed.summary}</p>
        </ResultBlock>
      )}

      {parsed.guidance.length > 0 && (
        <ResultBlock title={t("results.guidance")} variant="guidance" icon={IconCheck}>
          <ul>
            {parsed.guidance.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </ResultBlock>
      )}

      {parsed.medications.length > 0 && !medications?.length && (
        <ResultBlock title={t("results.medications")} variant="plan" icon={IconPrescription}>
          <ul className="dose-list">
            {parsed.medications.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </ResultBlock>
      )}

      {parsed.redFlags.length > 0 && (
        <ResultBlock title={t("results.redFlags")} variant="danger" icon={IconAlert}>
          <ul>
            {parsed.redFlags.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </ResultBlock>
      )}

      {parsed.sources.length > 0 && (
        <ResultBlock title={t("results.sources")} variant="sources" icon={IconDoc}>
          <ul className="source-refs">
            {parsed.sources.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </ResultBlock>
      )}

      <MedicationCards medications={medications} />

      {(finalPlan.treatment || finalPlan.additional_tests?.length > 0) && (
        <ResultBlock title={t("results.supervisorPlan")} variant="plan" icon={IconShield}>
          {finalPlan.treatment && (
            <>
              <h4>{t("results.treatmentPlan")}</h4>
              <p>{finalPlan.treatment}</p>
            </>
          )}
          {finalPlan.additional_tests?.length > 0 && (
            <>
              <h4>{t("results.suggestedTests")}</h4>
              <div className="test-chips">
                {finalPlan.additional_tests.map((test, i) => (
                  <span key={i} className="test-chip">{test}</span>
                ))}
              </div>
            </>
          )}
        </ResultBlock>
      )}
    </div>
  );
}

function MedicalForm() {
  const { t, i18n } = useTranslation();
  const { idToken } = useAuth();
  const fileRef = useRef(null);

  const [userInput, setUserInput] = useState("");
  const [inputType, setInputType] = useState("Symptoms");
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(0);
  const [patientAge, setPatientAge] = useState("");
  const [patientWeight, setPatientWeight] = useState("");
  const [patientGender, setPatientGender] = useState("All");

  const langCode = i18n.language?.split("-")[0] || "en";

  const inputTypes = [
    { id: "Symptoms", label: t("form.symptoms"), Icon: IconSymptoms },
    { id: "Prescription Review", label: t("form.prescription"), Icon: IconPrescription },
    { id: "Test Results", label: t("form.testResults"), Icon: IconLab },
  ];

  const handleVoiceTranscript = useCallback((text) => {
    setUserInput(text);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    setPipelineStep(0);

    const stepTimer = setInterval(() => {
      setPipelineStep((s) => Math.min(s + 1, 2));
    }, 3500);

    try {
      const data = await analyzeMedicalCase({
        userInput,
        inputType,
        file,
        idToken,
        language: langCode,
        patientAge,
        patientWeightKg: patientWeight,
        patientGender,
      });
      setResult(data);
    } catch (err) {
      setError(err.message || "Medical analysis failed");
    } finally {
      clearInterval(stepTimer);
      setLoading(false);
      setPipelineStep(2);
    }
  };

  const applyExample = (example) => {
    if (INPUT_TYPE_IDS.includes(example.type)) setInputType(example.type);
    setUserInput(example.text);
  };

  return (
    <div className="layout">
      <section className="panel panel--input">
        <div className="panel__head panel__head--input">
          <span className="panel__badge">01</span>
          <div>
            <h2>{t("form.inputTypeLegend")}</h2>
            <p className="muted">{t("app.tagline")}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="case-form">
          <div className="segmented" role="tablist">
            {inputTypes.map(({ id, label, Icon }) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={inputType === id}
                className={`segmented__item ${inputType === id ? "is-active" : ""}`}
                onClick={() => setInputType(id)}
              >
                <Icon />
                {label}
              </button>
            ))}
          </div>

          <div className="field patient-fields">
            <label>{t("patient.title")} <span className="muted">{t("patient.optional")}</span></label>
            <div className="patient-card">
            <div className="patient-grid">
              <input
                type="number"
                min="0"
                max="120"
                placeholder={t("patient.age")}
                value={patientAge}
                onChange={(e) => setPatientAge(e.target.value)}
                className="input-sm"
              />
              <input
                type="number"
                min="1"
                max="300"
                step="0.1"
                placeholder={t("patient.weight")}
                value={patientWeight}
                onChange={(e) => setPatientWeight(e.target.value)}
                className="input-sm"
              />
              <select
                value={patientGender}
                onChange={(e) => setPatientGender(e.target.value)}
                className="input-sm"
              >
                <option value="All">{t("patient.genderAll")}</option>
                <option value="Female">{t("patient.genderFemale")}</option>
                <option value="Male">{t("patient.genderMale")}</option>
              </select>
            </div>
            </div>
          </div>

          <div className="field">
            <div className="field__row">
              <label htmlFor="case-input">{t("form.caseLabel")}</label>
              <VoiceInputButton
                onTranscript={handleVoiceTranscript}
                baseText={userInput}
                disabled={loading}
              />
            </div>
            <textarea
              id="case-input"
              className="textarea"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder={t("form.casePlaceholder")}
              required
              rows={6}
            />
            <div className="examples">
              <span className="examples__label">{t("form.tryExample")}</span>
              {EXAMPLE_QUERIES.map((ex, i) => (
                <button key={i} type="button" className="example-btn" onClick={() => applyExample(ex)}>
                  {t(ex.labelKey)}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label>
              {t("form.attachLabel")} <span className="muted">{t("form.optional")}</span>
            </label>
            <div
              className={`upload ${dragOver ? "is-drag" : ""} ${file ? "has-file" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                const f = e.dataTransfer.files?.[0];
                if (f) setFile(f);
              }}
              onClick={() => fileRef.current?.click()}
              onKeyDown={(e) => e.key === "Enter" && fileRef.current?.click()}
              role="button"
              tabIndex={0}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.txt"
                hidden
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              <IconUpload />
              {file ? (
                <>
                  <span className="upload__name">{file.name}</span>
                  <button
                    type="button"
                    className="btn-text btn-text--danger"
                    onClick={(e) => { e.stopPropagation(); setFile(null); }}
                  >
                    {t("form.removeFile")}
                  </button>
                </>
              ) : (
                <>
                  <span>{t("form.dropHint")}</span>
                  <span className="muted">{t("form.dropBrowse")}</span>
                </>
              )}
            </div>
          </div>

          <button type="submit" className="btn-primary" disabled={loading || !userInput.trim()}>
            {loading ? (
              <>
                <span className="btn-primary__spin" />
                {t("form.analyzing")}
              </>
            ) : (
              <>
                {t("form.submit")}
                <IconArrow />
              </>
            )}
          </button>
        </form>
      </section>

      <section className="panel panel--output">
        <div className="panel__head panel__head--sticky panel__head--output">
          <span className="panel__badge panel__badge--alt">02</span>
          <div>
            <h2>{t("results.title")}</h2>
            <p className="muted">{t("results.subtitle")}</p>
          </div>
        </div>

        <div className="panel__body">
          {loading && <Pipeline step={pipelineStep} />}

          {!loading && error && (
            <div className="result-alert result-alert--error">
              <IconAlert />
              <div>
                <h3>{t("results.failed")}</h3>
                <p>{error}</p>
              </div>
            </div>
          )}

          {!loading && !error && !result && (
            <div className="empty-state">
              <div className="empty-state__hero">
                <div className="empty-state__icon"><IconDoc /></div>
                <h3>{t("results.readyTitle")}</h3>
                <p>{t("results.readyText")}</p>
              </div>
              <div className="empty-state__features">
                <div className="feature-card"><IconShield /><span>{t("results.feature1")}</span></div>
                <div className="feature-card"><IconDoc /><span>{t("results.feature2")}</span></div>
                <div className="feature-card"><IconCheck /><span>{t("results.feature3")}</span></div>
              </div>
            </div>
          )}

          {!loading && result && <ResultView data={result} langCode={langCode} />}
        </div>
      </section>
    </div>
  );
}

export default MedicalForm;
