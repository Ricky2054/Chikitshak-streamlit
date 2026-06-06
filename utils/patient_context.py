"""Build patient context string for agent prompts."""


def build_patient_context(age=None, weight_kg=None, gender=None) -> str:
    parts = []
    if age not in (None, ""):
        parts.append(f"Age: {age} years")
    if weight_kg not in (None, ""):
        parts.append(f"Weight: {weight_kg} kg")
    if gender and gender not in ("", "All"):
        parts.append(f"Gender: {gender}")
    if not parts:
        return "Patient details not provided."
    return "; ".join(parts) + "."


def patient_dict(age=None, weight_kg=None, gender=None) -> dict:
    return {
        "age": age,
        "weight_kg": weight_kg,
        "gender": gender or "All",
    }
