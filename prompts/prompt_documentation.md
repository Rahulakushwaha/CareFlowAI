# CareFlow AI — Prompt Engineering Documentation

## Purpose
This document records the prompts used in the project and illustrates how prompt constraints can improve an administrative response workflow. Some examples below are proposed assessment prompts, not a claim that every prompt was executed as a separate experiment.

## 1. Project-generation prompt
> Build a complete, beginner-friendly Python Streamlit healthcare inquiry automation app with a dashboard, inquiry intake, inquiry management, response drafting, analytics, SQLite persistence, optional AI integration, tests, README, and prompt documentation. Keep it safe: no diagnosis or treatment recommendations, and use fictional sample data.

## 2. Initial classification prompt (baseline example)
> Read this clinic inquiry and write a response.

**Weakness:** This does not define output fields, allowed categories, safety boundaries, tone, or review requirements.

## 3. Improved structured prompt
> You are a healthcare administrative assistant. Classify the inquiry as exactly one of Appointments, Clinic Hours, Billing, General Inquiry, or Clinical Question. Return JSON with category, summary, priority (Low, Medium, High), and draft_response. Use concise, empathetic language. Never diagnose, recommend medication, or give treatment advice. For clinical questions, direct the person to a qualified healthcare professional and advise emergency services for urgent or life-threatening symptoms. Do not claim that an appointment or billing action is confirmed. The response is a draft for human review only.

**Improvements:** Allowed labels reduce category drift; JSON makes output easier to process; safety constraints reduce the risk of inappropriate clinical responses; human review prevents automatic sending.

## 4. Follow-up prompt examples
These are suggested iteration prompts to use during development. Record the actual outcomes if you run them:
- “Handle blank messages and malformed email addresses gracefully; add validation and user-friendly messages.”
- “Ensure clinical questions never receive a diagnosis or treatment recommendation, including when AI API output is malformed.”
- “If no API key exists or the API fails, clearly use deterministic demo responses and label the mode accurately.”
- “Add tests for database create/read/update behavior, validation, fallback mode, and CSV export.”
- “Review the interface for accessible contrast, consistent spacing, empty states, and clear human-review messaging.”

## 5. Example
**Fictional input:** “Could you tell me whether the clinic is open on Saturday?”

**Expected category:** Clinic Hours  
**Expected summary:** “Asks whether the clinic is open on Saturday.”  
**Illustrative draft:** “Thank you for your inquiry about clinic hours. Our team will confirm the current opening hours and any holiday changes with you shortly.”

This is an illustrative rule-based demo response, not proof of a live AI API call.

## 6. AI mode transparency
- **DEMO MODE:** deterministic keyword rules and response templates; no language model is called.
- **AI API mode:** uses the configured OpenAI-compatible API when credentials are present and a request succeeds.
- If API execution fails, the app falls back to rule-based behavior. Users should not describe fallback output as model-generated.
