export async function analyzeMedicalCase({
  userInput,
  inputType,
  file,
  idToken,
  language,
  patientAge,
  patientWeightKg,
  patientGender,
}) {
  const BASE_URL = import.meta.env.VITE_API_URL || "";
  const API_URL = `${BASE_URL}/api/medical/analyze`;
  const formData = new FormData();
  formData.append("user_input", userInput);
  formData.append("input_type", inputType);
  formData.append("language", language || "en");
  if (patientAge) formData.append("patient_age", String(patientAge));
  if (patientWeightKg) formData.append("patient_weight_kg", String(patientWeightKg));
  if (patientGender) formData.append("patient_gender", patientGender);
  if (file) {
    formData.append("file", file);
  }

  const headers = {};
  if (idToken) {
    headers.Authorization = `Bearer ${idToken}`;
  }

  const res = await fetch(API_URL, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!res.ok) {
    let detail = "Medical analysis failed";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return await res.json();
}
