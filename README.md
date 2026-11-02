# CareFlow AI — Healthcare Inquiry Automation

CareFlow AI is a Streamlit prototype for managing clinic administrative inquiries. It demonstrates AI-assisted categorization, response drafting, prompt engineering, inquiry tracking, analytics, and CSV export.

> **Safety notice:** This is an assessment prototype, not a certified healthcare product. It does not diagnose or recommend treatment. Clinical questions are routed to qualified healthcare professionals. Use fictional data for demos; do not enter real patient health information.

## Features
- Dashboard metrics and Plotly charts
- Inquiry intake form and validation
- SQLite persistence and inquiry status updates
- Search and category/status filtering
- AI Response Studio with editable draft responses
- Optional OpenAI-compatible API integration
- Clearly labeled rule-based demo fallback when no API key is configured
- Analytics and CSV export
- Prompt engineering documentation
- Pytest tests

## Run on Windows
Open PowerShell or the Cursor terminal in the project folder.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate the environment again.

## Optional live AI configuration
1. Copy `.env.example` to `.env`.
2. Add your own `OPENAI_API_KEY` and optionally set `OPENAI_MODEL`.
3. Install dependencies and restart Streamlit.

The app does not automatically load `.env`; if you want `.env` loading, install `python-dotenv` and add `load_dotenv()` at startup, or configure environment variables in your terminal. Never commit API keys. Without credentials, the app uses transparent rule-based DEMO MODE.

## Tests
```powershell
pytest -q
```

## Suggested demo flow
1. Open Dashboard and load fictional demo records.
2. Submit an inquiry.
3. Open Manage Inquiries and update its status.
4. Open AI Response Studio and generate a response draft.
5. Review and edit the draft before saving.
6. Open Analytics & Reports and export the CSV.
7. Explain the prompt iterations in `prompts/prompt_documentation.md`.

## Architecture
- `app.py`: Streamlit UI and page navigation
- `database.py`: SQLite persistence and CRUD operations
- `ai_engine.py`: classification, safe fallback responses, optional AI API
- `utils.py`: validation and CSV export
- `tests/`: automated checks
- `prompts/`: prompt documentation and system prompt

## Limitations
- Demo mode uses rules and templates, not a language model.
- Priority assignment is a simple illustrative heuristic, not a clinical triage system.
- No messages are sent automatically.
- The prototype has not been assessed for production privacy, security, compliance, or clinical use.
