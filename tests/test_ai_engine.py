from ai_engine import classify_message, fallback_reply, process_inquiry

def test_appointment_classification():
    category,priority=classify_message("I want to book an appointment")
    assert category == "Appointments"
    assert priority in {"Low","Medium","High"}

def test_clinical_safety():
    category,_=classify_message("I have symptoms and need treatment advice")
    assert category == "Clinical Question"
    reply=fallback_reply("I need treatment advice",category).lower()
    assert "qualified healthcare professional" in reply
    assert "diagnose" not in reply

def test_fallback_has_required_fields(monkeypatch):
    monkeypatch.setattr("ai_engine.API_MODE",False)
    result=process_inquiry("Are you open on Saturday?","Clinic Hours")
    assert {"category","priority","summary","draft_response"} <= set(result)
