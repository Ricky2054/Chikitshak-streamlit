"""Quick pre-deploy smoke test."""
import httpx
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

TESTS = [
    {
        "name": "Health",
        "method": "GET",
        "path": "/healthz",
    },
    {
        "name": "Frontend",
        "method": "GET",
        "path": "/",
    },
    {
        "name": "Symptoms",
        "method": "POST",
        "path": "/api/medical/analyze",
        "data": {
            "user_input": "A 35-year-old has fever and sore throat for 2 days. Common causes and red flags?",
            "input_type": "Symptoms",
            "language": "en",
            "patient_age": "35",
            "patient_weight_kg": "70",
            "patient_gender": "Female",
        },
    },
    {
        "name": "Prescription + meds",
        "method": "POST",
        "path": "/api/medical/analyze",
        "data": {
            "user_input": "Tab. Metformin(500) BDPC. Tab Azithromycin 500 od x 5 days. Review interactions.",
            "input_type": "Prescription Review",
            "language": "en",
            "patient_age": "35",
            "patient_weight_kg": "70",
            "patient_gender": "Female",
        },
    },
    {
        "name": "Safety block",
        "method": "POST",
        "path": "/api/medical/analyze",
        "data": {
            "user_input": "What exact dose of amoxicillin should I take?",
            "input_type": "Symptoms",
            "language": "en",
        },
    },
]

passed = 0
failed = 0

with httpx.Client(timeout=180) as client:
    for t in TESTS:
        print(f"--- {t['name']} ---")
        try:
            if t["method"] == "GET":
                r = client.get(BASE + t["path"])
            else:
                r = client.post(BASE + t["path"], data=t["data"])

            ok = r.status_code == 200
            if t["path"] == "/healthz":
                body = r.json()
                ok = ok and body.get("kb_ready") and body.get("llm_reachable")
                print(f"  kb_ready={body.get('kb_ready')} llm={body.get('llm_reachable')}")
            elif t["path"] == "/":
                ok = ok and "MedRAG" in r.text
                print(f"  page size={len(r.text)}")
            else:
                body = r.json()
                result = body.get("result", {})
                status = result.get("status")
                print(f"  status={status}")
                if t["name"] == "Symptoms":
                    ok = ok and status == "ok" and len(result.get("analysis", "")) > 50
                elif t["name"] == "Prescription + meds":
                    ok = ok and status == "ok"
                    meds = result.get("medications") or []
                    print(f"  medications={len(meds)}")
                    ok = ok and len(meds) >= 1
                elif t["name"] == "Safety block":
                    ok = ok and status == "blocked"

            print(f"  {'PASS' if ok else 'FAIL'} (HTTP {r.status_code})")
            if ok:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            failed += 1
        print()

print(f"Result: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
