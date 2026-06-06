"""Language helpers for multilingual medical responses."""

from __future__ import annotations

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "bn": "Bengali",
    "kn": "Kannada",
    "ml": "Malayalam",
    "es": "Spanish",
    "ar": "Arabic",
    "fr": "French",
}

BLOCKED_MESSAGES: dict[str, str] = {
    "en": (
        "Direct prescribing or personal dosing requests cannot be processed. "
        "Describe symptoms, upload a prescription for review, or share test results instead."
    ),
    "hi": (
        "मैं विशिष्ट दवाएं या खुराक निर्देश देने में मदद नहीं कर सकता। "
        "मैं ज्ञान आधार से सामान्य शैक्षिक जानकारी साझा कर सकता हूं और एक चिकित्सक से चर्चा करने के लिए सुझाव दे सकता हूं।"
    ),
    "ta": (
        "குறிப்பitic மருந்துகள் அல்லது dosage வழிகாட்டுதல்களை வழங்க என்னால் முடியாது. "
        "பொது கல்வி தகவல்களைப் பகிர்ந்து, மருத்துவரிடம் கலந்தாலோசிக்க பரிந்துரைக்க முடியும்."
    ),
    "te": (
        "నిర్దిష్ట మందులు లేదా మోతాదు సూచనలు అందించడంలో నేను సహాయం చేయలేను. "
        "సాధారణ విద్యా సమాచారం షేర్ చేసి, వైద్యుడితో చర్చించమని సూచించగలను."
    ),
    "mr": (
        "विशिष्ट औषधे किंवा डोस सूचना देण्यात मी मदत करू शकत नाही. "
        "मी सामान्य शैक्षणिक माहिती शेअर करू शकतो आणि डॉक्टरांशी चर्चा करण्याचा सल्ला देऊ शकतो."
    ),
    "bn": (
        "নির্দিষ্ট ওষুধ বা ডোজ নির্দেশ দিতে আমি সাহায্য করতে পারি না। "
        "আমি সাধারণ শিক্ষামূলক তথ্য শেয়ার করতে পারি এবং একজন চিকিৎসকের সাথে আলোচনার পরামর্শ দিতে পারি।"
    ),
    "es": (
        "No puedo ayudar con medicamentos específicos ni instrucciones de dosificación. "
        "Puedo compartir información educativa general y sugerir qué discutir con un médico."
    ),
    "ar": (
        "لا يمكنني المساعدة في وصف أدوية محددة أو تعليمات الجرعات. "
        "يمكنني مشاركة معلومات تعليمية عامة واقتراح ما يجب مناقشته مع طبيب."
    ),
    "fr": (
        "Je ne peux pas aider avec des médicaments spécifiques ou des instructions de dosage. "
        "Je peux partager des informations éducatives générales et suggérer quoi discuter avec un clinicien."
    ),
}


def normalize_language(code: str | None) -> str:
    if not code:
        return "en"
    base = code.strip().lower().split("-")[0]
    return base if base in SUPPORTED_LANGUAGES else "en"


def language_name(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(normalize_language(code), "English")


def llm_language_instruction(code: str) -> str:
    lang = normalize_language(code)
    if lang == "en":
        return ""
    name = language_name(lang)
    return (
        f"\nIMPORTANT: Write all medical content in {name}. "
        f"Keep these section headers exactly in English: Summary, Guidance, Red Flags, Sources, "
        f"Treatment Plan, Additional Tests."
    )


def blocked_message(code: str) -> str:
    lang = normalize_language(code)
    return BLOCKED_MESSAGES.get(lang, BLOCKED_MESSAGES["en"])
