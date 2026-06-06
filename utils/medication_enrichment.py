"""Fetch generic drug info, pill images (NLM RxImage), and protocol-based dosing notes."""



from __future__ import annotations



import re

from typing import Any



import httpx



# Common drugs from OPD protocols + dataset (brand → generic hint)

DRUG_ALIASES: dict[str, str] = {

    "levoflox": "levofloxacin",

    "cifran": "ciprofloxacin",

    "metrogyl": "metronidazole",

    "pcm": "paracetamol",

    "paracetamol": "paracetamol",

    "acetaminophen": "paracetamol",

    "brufen": "ibuprofen",

    "pan": "pantoprazole",

    "pantop": "pantoprazole",

    "pantoprazole": "pantoprazole",

    "azithromycin": "azithromycin",

    "azithral": "azithromycin",

    "amoxyclav": "amoxicillin clavulanate",

    "augmentin": "amoxicillin clavulanate",

    "amoxicillin": "amoxicillin",

    "metformin": "metformin",

    "glycomet": "metformin",

    "glimepride": "glimepiride",

    "glimepiride": "glimepiride",

    "amlodipine": "amlodipine",

    "nitrofurantoin": "nitrofurantoin",

    "doxycycline": "doxycycline",

    "cefixime": "cefixime",

    "vertin": "betahistine",

    "stematil": "prochlorperazine",

    "naxdom": "naproxen",

    "zerodol": "aceclofenac",

    "pregabalin": "pregabalin",

    "omeprazole": "omeprazole",

    "ibuprofen": "ibuprofen",

    "racecadrotil": "racecadotril",

    "montelukast": "montelukast",

    "levocetirizine": "levocetirizine",

    "amitriptyline": "amitriptyline",

    "labetalol": "labetalol",

    "clonazepam": "clonazepam",

    "ciprofloxacin": "ciprofloxacin",

    "levofloxacin": "levofloxacin",

    "metronidazole": "metronidazole",

}



KNOWN_GENERICS = set(DRUG_ALIASES.values()) | set(DRUG_ALIASES.keys())



DRUG_SUFFIX = re.compile(

    r"(?:cillin|mycin|azole|pril|sartan|olol|pine|fenac|idine|oxacin|prazole|formin|pam|zepam|lol)$",

    re.IGNORECASE,

)



STOP_WORDS = {

    "up", "od", "bd", "tds", "bdpc", "days", "day", "once", "twice", "wice",

    "mg", "ml", "tab", "cap", "syr", "inj", "after", "before", "food", "meal",

    "x", "for", "with", "and", "the", "oral", "daily",

}



FREQ_MAP = {

    "od": "once daily",

    "bd": "twice daily",

    "tds": "three times daily",

    "qid": "four times daily",

    "bdpc": "twice daily after meals",

    "hs": "at bedtime",

    "sos": "as needed",

}



# Educational weight-based reference (not prescribing)

WEIGHT_DOSE_RULES: dict[str, dict[str, Any]] = {

    "paracetamol": {"per_kg_mg": 15, "max_single_mg": 1000, "interval": "every 6 hours"},

    "ibuprofen": {"per_kg_mg": 10, "max_single_mg": 400, "interval": "every 8 hours"},

    "amoxicillin": {"per_kg_day_mg": 40, "max_day_mg": 3000, "divisions": 3},

    "azithromycin": {"per_kg_day_mg": 10, "max_day_mg": 500, "duration_days": 3},

    "metronidazole": {"per_kg_day_mg": 30, "max_day_mg": 2000, "divisions": 3},

    "ciprofloxacin": {"per_kg_day_mg": 20, "max_day_mg": 1500, "divisions": 2},

}

STANDARD_ADULT_DOSES: dict[str, str] = {
    "paracetamol": "500-1000 mg every 6 hours (max 4 g/day)",
    "ibuprofen": "400 mg every 8 hours with food",
    "azithromycin": "500 mg once daily for 3 days",
    "metformin": "500 mg twice daily after meals",
    "amoxicillin": "500 mg three times daily for 5-7 days",
    "amoxicillin clavulanate": "625 mg twice daily for 5-7 days",
    "nitrofurantoin": "100 mg twice daily for 5-7 days",
    "pantoprazole": "40 mg once daily before breakfast",
    "omeprazole": "20-40 mg once daily before meals",
    "amlodipine": "5 mg once daily",
    "ciprofloxacin": "500 mg twice daily for 7-14 days",
    "levofloxacin": "500 mg once daily for 7-10 days",
    "metronidazole": "400 mg three times daily for 7 days",
    "doxycycline": "100 mg twice daily for 7 days",
    "cefixime": "400 mg once daily for 5-7 days",
    "pregabalin": "75 mg twice daily, titrate as needed",
    "montelukast": "10 mg once daily at night",
    "levocetirizine": "5 mg once daily",
}

LLM_MED_LINE = re.compile(
    r"^[\s]*[-•*]\s*([A-Za-z][A-Za-z0-9 /+-]{2,40}?)\s*:\s*(.+)$",
    re.MULTILINE,
)

LLM_MED_INLINE = re.compile(
    r"^[\s]*[-•*]\s*([A-Za-z][A-Za-z0-9/+ -]{2,30})\s+(\d+(?:\.\d+)?\s*(?:mg|ml|g|mcg)[^\n]*)",
    re.MULTILINE | re.IGNORECASE,
)

DOSE_IN_TEXT = re.compile(
    r"(\d+(?:\.\d+)?\s*(?:mg|ml|g|mcg)(?:\s*/\s*day)?(?:\s+(?:od|bd|tds|qid|once daily|twice daily|three times daily))?[^\n,.]{0,30})",
    re.IGNORECASE,
)



PRESCRIPTION_PATTERN = re.compile(

    r"(?:tab\.?|cap\.?|t\.?|syr\.?|inj\.?|mdi)\s*"

    r"([a-zA-Z][a-zA-Z0-9\-+/ ]{1,40}?)\s*"

    r"(?:[\(\[]\s*(\d+(?:\.\d+)?(?:\s*/\s*\d+)?)\s*[\)\]]|\s+(\d+(?:\.\d+)?(?:\s*/\s*\d+)?))"

    r"(?:\s*(mg|ml|g|mcg))?"

    r"(?:\s+([a-z]{2,6}))?"

    r"(?:\s*x\s*(\d+)\s*(?:days?|d))?",

    re.IGNORECASE,

)



MED_NAME_PATTERN = re.compile(

    r"\b("

    + "|".join(re.escape(n) for n in sorted(KNOWN_GENERICS, key=len, reverse=True))

    + r")\b",

    re.IGNORECASE,

)





def _normalize_generic(raw: str) -> str | None:

    key = raw.strip().lower()

    key = re.sub(r"[^a-z0-9+/ -]", "", key).strip()

    if not key or key in STOP_WORDS or len(key) < 3:

        return None

    first = key.split()[0]

    if first in STOP_WORDS:

        return None

    generic = DRUG_ALIASES.get(first) or DRUG_ALIASES.get(key) or key

    if generic in KNOWN_GENERICS or DRUG_SUFFIX.search(generic):

        return generic

    return None





def _format_dose(strength: str, unit: str, freq: str, duration: str) -> str:

    parts = []

    if strength:

        u = unit or "mg"

        parts.append(f"{strength} {u}")

    if freq:

        parts.append(FREQ_MAP.get(freq.lower(), freq))

    if duration:

        parts.append(f"for {duration} days")

    return " ".join(parts) if parts else "See institutional protocol"





def _age_band(age: int | None) -> str:

    if age is None:

        return "adult"

    if age <= 1:

        return "infant"

    if age <= 12:

        return "child"

    if age <= 17:

        return "adolescent"

    if age >= 65:

        return "elderly"

    return "adult"





def _standard_adult_dose(generic: str, band: str) -> str | None:
    dose = STANDARD_ADULT_DOSES.get(generic)
    if not dose:
        return None
    if band == "elderly":
        return f"{dose} (elderly: consider lower starting dose)"
    return dose


def _lookup_dose_from_docs(generic: str, doc_blob: str) -> str | None:
    if not doc_blob or not generic:
        return None
    g = generic.lower()
    best = None
    for line in doc_blob.splitlines():
        low = line.lower()
        if g not in low:
            continue
        if "FIRST_LINE_MEDICATIONS" in line or "mg" in low or " ml" in low:
            dm = DOSE_IN_TEXT.search(line)
            if dm:
                best = dm.group(1).strip()
                break
            parts = line.split(":", 1)
            if len(parts) == 2 and g in parts[1].lower():
                snippet = parts[1].strip()[:120]
                if dm := DOSE_IN_TEXT.search(snippet):
                    best = dm.group(1).strip()
                elif len(snippet) > 8:
                    best = snippet
    if not best:
        dm = re.search(
            rf"{re.escape(g)}[^.\n]{{0,60}}(\d+(?:\.\d+)?\s*(?:mg|ml)[^.\n]{{0,40}})",
            doc_blob,
            re.IGNORECASE,
        )
        if dm:
            best = dm.group(1).strip()
    return best


def _parse_llm_med_lines(blob: str) -> list[dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    section = re.search(
        r"Medications?:\s*(.+?)(?=\n\s*(?:Summary|Guidance|Red Flags|Sources):|\Z)",
        blob,
        re.DOTALL | re.IGNORECASE,
    )
    text = section.group(1) if section else blob
    if re.search(r"none\s+indicated", text, re.I):
        return []
    for match in LLM_MED_LINE.finditer(text):
        generic = _normalize_generic(match.group(1))
        if generic:
            found[generic] = {
                "name": generic,
                "protocol_dose": match.group(2).strip().rstrip("."),
                "raw": match.group(0).strip(),
            }
    for match in LLM_MED_INLINE.finditer(text):
        generic = _normalize_generic(match.group(1))
        if generic and generic not in found:
            found[generic] = {
                "name": generic,
                "protocol_dose": match.group(2).strip(),
                "raw": match.group(0).strip(),
            }
    return list(found.values())


def _resolve_dose(generic: str, parsed_dose: str, doc_blob: str, band: str) -> str:
    if parsed_dose and parsed_dose not in ("", "See institutional protocol"):
        return parsed_dose
    doc_dose = _lookup_dose_from_docs(generic, doc_blob)
    if doc_dose:
        return doc_dose
    adult = _standard_adult_dose(generic, band)
    if adult:
        return adult
    return "See institutional protocol"


def _weight_based_dose(generic: str, weight_kg: float | None, band: str) -> str | None:

    rule = WEIGHT_DOSE_RULES.get(generic)

    if not rule or not weight_kg or band not in {"infant", "child", "adolescent"}:

        if band in {"adult", "elderly", "adolescent"} and weight_kg and weight_kg >= 40:
            return _standard_adult_dose(generic, band)
        return None

    if "per_kg_mg" in rule:

        dose = min(round(weight_kg * rule["per_kg_mg"]), rule["max_single_mg"])

        return f"~{dose} mg per dose ({rule['per_kg_mg']} mg/kg), {rule['interval']} (weight-based reference)"

    if "per_kg_day_mg" in rule:

        daily = min(round(weight_kg * rule["per_kg_day_mg"]), rule["max_day_mg"])

        per_dose = round(daily / rule.get("divisions", 1))

        extra = ""

        if rule.get("duration_days"):

            extra = f" for {rule['duration_days']} days"

        return f"~{daily} mg/day (~{per_dose} mg per dose){extra} (weight-based reference)"

    return None





def _personalized_note(

    age: int | None,

    weight_kg: float | None,

    gender: str | None,

    dose_text: str,

    suggested: str | None,

) -> str:

    band = _age_band(age)

    parts = [f"Reference protocol dose: {dose_text}"]

    if suggested:

        parts.append(f"Weight/age-adjusted reference: {suggested}")

    if band in {"child", "infant"}:

        parts.append("Pediatric: weight-based adjustment usually required — confirm with pediatrician.")

    if band == "elderly":

        parts.append("Elderly: consider renal/hepatic dose reduction.")

    if band == "adolescent":

        parts.append("Adolescent: adult doses may apply when weight ≥40 kg.")

    if weight_kg and weight_kg < 50 and band == "adult":

        parts.append(f"Low body weight ({weight_kg} kg): clinician may use lower end of dose range.")

    if gender and gender.lower() == "female":

        parts.append("Check pregnancy/lactation status before dispensing.")

    return " ".join(parts)





def _parse_prescription_lines(blob: str) -> list[dict[str, str]]:

    found: dict[str, dict[str, str]] = {}

    for match in PRESCRIPTION_PATTERN.finditer(blob):

        raw_name = match.group(1).strip()

        strength = match.group(2) or match.group(3) or ""

        unit = (match.group(4) or "mg").lower()

        freq = (match.group(5) or "").lower()

        duration = match.group(6) or ""

        generic = _normalize_generic(raw_name)

        if not generic:

            continue

        dose = _format_dose(strength, unit, freq, duration)

        found[generic] = {"name": generic, "protocol_dose": dose, "raw": match.group(0).strip()}

    return list(found.values())





def _parse_known_names(blob: str) -> list[dict[str, str]]:

    found: dict[str, dict[str, str]] = {}

    for match in MED_NAME_PATTERN.finditer(blob):

        generic = _normalize_generic(match.group(1))

        if generic and generic not in found:

            found[generic] = {"name": generic, "protocol_dose": "", "raw": match.group(0)}

    return list(found.values())





def extract_medications_from_text(analysis: str, doc_blob: str = "") -> list[dict[str, str]]:

    """Prefer medications from LLM analysis; supplement from KB snippets only if needed."""

    found: dict[str, dict[str, str]] = {}



    for med in _parse_prescription_lines(analysis):

        found[med["name"]] = med

    for med in _parse_llm_med_lines(analysis):

        if med["name"] not in found or not found[med["name"]].get("protocol_dose"):

            found[med["name"]] = med

    for med in _parse_known_names(analysis):

        if med["name"] not in found:

            found[med["name"]] = med



    if len(found) < 3 and doc_blob:

        # Only scan doc lines that mention drugs already found or explicit Rx patterns

        for med in _parse_prescription_lines(doc_blob[:12000]):

            if med["name"] not in found:

                found[med["name"]] = med

        if not found:

            for med in _parse_known_names(doc_blob[:8000]):

                if med["name"] not in found:

                    found[med["name"]] = med



    return list(found.values())[:6]





async def _rxnorm_lookup(name: str) -> tuple[str | None, str | None]:

    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={name}&search=2"

    try:

        async with httpx.AsyncClient(timeout=8.0) as client:

            r = await client.get(url)

            if r.status_code != 200:

                return None, None

            data = r.json()

            ids = data.get("idGroup", {}).get("rxnormId", [])

            if not ids:

                approx = f"https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term={name}&maxEntries=1"

                r2 = await client.get(approx)

                if r2.status_code == 200:

                    cand = r2.json().get("approximateGroup", {}).get("candidate", [])

                    if cand:

                        ids = [cand[0].get("rxcui")]

            if not ids:

                return None, None

            rxcui = str(ids[0] if isinstance(ids, list) else ids)

            r3 = await client.get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/property.json?propName=RxNorm%20Name")

            generic_name = name

            if r3.status_code == 200:

                props = r3.json().get("propConceptGroup", {}).get("propConcept", [])

                if props:

                    generic_name = props[0].get("propValue", name)

            return rxcui, generic_name

    except Exception:

        return None, None





async def _fetch_pill_image(rxcui: str) -> tuple[str | None, str | None]:

    url = f"https://rximage.nlm.nih.gov/api/rximage/1/rxnav?rxcui={rxcui}"

    try:

        async with httpx.AsyncClient(timeout=10.0) as client:

            r = await client.get(url)

            if r.status_code == 200:

                images = r.json().get("nlmRxImages", [])

                if images and images[0].get("imageUrl"):

                    return images[0]["imageUrl"], "NLM RxImage"

    except Exception:

        pass

    return None, None





async def _wikipedia_image(name: str) -> tuple[str | None, str | None]:

    slug = name.replace(" ", "_").title()

    for variant in (slug, name.replace(" ", "_")):

        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{variant}"

        try:

            async with httpx.AsyncClient(timeout=6.0) as client:

                r = await client.get(url)

                if r.status_code == 200:

                    thumb = r.json().get("thumbnail", {})

                    if thumb.get("source"):

                        return thumb["source"], "Wikipedia"

        except Exception:

            pass

    return None, None





async def _commons_pill_image(name: str) -> tuple[str | None, str | None]:

    query = f"{name} pill tablet"

    url = (

        "https://commons.wikimedia.org/w/api.php"

        f"?action=query&generator=search&gsrsearch={query}&gsrnamespace=6"

        "&prop=imageinfo&iiprop=url&iiurlwidth=320&format=json"

    )

    try:

        async with httpx.AsyncClient(timeout=8.0) as client:

            r = await client.get(url)

            if r.status_code == 200:

                pages = r.json().get("query", {}).get("pages", {})

                for page in pages.values():

                    info = (page.get("imageinfo") or [{}])[0]

                    src = info.get("thumburl") or info.get("url")

                    if src:

                        return src, "Wikimedia Commons"

    except Exception:

        pass

    return None, None





async def _resolve_image(rxcui: str | None, generic_name: str) -> tuple[str | None, str | None]:

    if rxcui:

        img, src = await _fetch_pill_image(rxcui)

        if img:

            return img, src

    for fetcher in (_wikipedia_image, _commons_pill_image):

        img, src = await fetcher(generic_name)

        if img:

            return img, src

    return None, None





async def enrich_medications(

    analysis: str,

    relevant_docs: list[str] | None,

    patient: dict[str, Any] | None = None,

) -> list[dict[str, Any]]:

    patient = patient or {}

    age = patient.get("age")

    try:

        age = int(age) if age not in (None, "") else None

    except (TypeError, ValueError):

        age = None

    weight = patient.get("weight_kg")

    try:

        weight = float(weight) if weight not in (None, "") else None

    except (TypeError, ValueError):

        weight = None

    gender = patient.get("gender") or "All"

    band = _age_band(age)



    doc_blob = "\n".join(relevant_docs or [])[:20000]

    meds = extract_medications_from_text(analysis, doc_blob)

    if not meds:

        return []



    enriched: list[dict[str, Any]] = []

    for med in meds:

        name = med["name"]

        rxcui, generic_name = await _rxnorm_lookup(name)

        image_url, image_source = await _resolve_image(rxcui, generic_name or name)



        raw_dose = med.get("protocol_dose") or ""

        dose = _resolve_dose(name, raw_dose, doc_blob, band)

        suggested = _weight_based_dose(name, weight, band)

        display_dose = suggested if suggested and band in {"infant", "child"} else dose

        enriched.append(

            {

                "name": name,

                "generic_name": (generic_name or name).title(),

                "rxcui": rxcui,

                "image_url": image_url,

                "protocol_dose": dose,

                "suggested_dose": suggested,

                "display_dose": display_dose,

                "personalized_note": _personalized_note(age, weight, gender, display_dose, suggested),

                "image_source": image_source,

            }

        )

    return enriched


