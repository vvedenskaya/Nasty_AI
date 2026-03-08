# NASTY AI — Comprehensive Project Breakdown

## 1. Project Overview

### What problem this project solves
`NASTY AI` solves the problem of building a chatbot that is more than a basic text generator. It combines:
- a strong, consistent AI persona,
- practical security-oriented tools,
- persistent user memory,
- a themed frontend experience,
- and production-style Raspberry Pi deployment.

The purpose is both practical and educational: demonstrate how to design a complete AI product where UX, backend logic, memory, and deployment all work together.

### Overall architecture and how parts connect
The project follows a clear full-stack pattern:
- **Frontend** (`templates/index.html`, `static/script.js`, `static/style.css`)
  - Matrix-style chat UI, command suggestions, and API calls.
- **Backend API** (`app2.py`)
  - Flask routes for chat and tool endpoints.
  - Anthropic integration for LLM responses and persona behavior.
  - Session/user handling and DB persistence.
- **Tool layer** (`tools.py`)
  - Deterministic utility functions (OSINT links, password checks, security news, surveillance links).
- **Database**
  - SQLite via SQLAlchemy for persistent memory per user.
- **Deployment layer** (`pi_setup/`)
  - systemd + desktop autostart + browser launcher for kiosk mode on Raspberry Pi.

---

## 2. Technologies & Stack

### Backend
- **Python 3.12** (`runtime.txt`, `pyproject.toml`)
  - Main language for API logic, memory processing, and integrations.
- **Flask**
  - Web server and routing.
- **Flask-SQLAlchemy**
  - ORM for DB access.
- **SQLAlchemy MutableDict / MutableList**
  - Tracks in-place changes inside JSON columns for memory objects.
- **SQLite**
  - Lightweight local database for user profile/topic/chat memory.

### AI layer
- **Anthropic Python SDK** (`anthropic`)
  - Calls Claude models for:
    - main chat response,
    - profile extraction,
    - topic summary extraction,
    - OSINT commentary.
- **Anthropic tool use (`web_search_20250305`)**
  - Allows model-triggered web search in regular chat flow.

### Utility and integrations
- **requests**
  - HTTP API calls (password breach checks, URL security checks).
- **feedparser**
  - RSS parsing for cybersecurity news.
- **hashlib**
  - SHA1 hashing for k-anonymity password breach lookup flow.
- **re / json / random / uuid / datetime / pathlib**
  - Parsing, formatting, IDs, randomization, timestamps, file/env operations.

### Frontend
- **HTML/CSS/Vanilla JavaScript**
  - Fast, framework-free UI.
- **Canvas API**
  - Matrix rain visual effect.
- **Fetch API**
  - Browser-to-backend communication.
- **localStorage**
  - Stores user ID between sessions.
- **PowerGlitch (CDN import)**
  - Visual glitch effect on send button.

### Deployment and operations
- **systemd** (`pi_setup/wasp_bot.service`)
  - Auto-start backend, restart on failure.
- **Desktop autostart** (`pi_setup/wasp_bot_browser.desktop`)
  - Launches browser on desktop login.
- **Bash launcher** (`pi_setup/wasp-bot-browser.sh`)
  - Waits for server readiness, configures display behavior, starts Chromium.
- **curl / chromium-browser / xset**
  - Health checks, kiosk browser launch, screen power/blank settings.

---

## 3. Key Concepts & Skills Demonstrated

### Programming concepts and patterns used
- **RESTful endpoint design** for chat and tools.
- **Stateful chat memory** with layered architecture:
  - profile facts,
  - topic summaries,
  - recent chat history.
- **Session management**
  - Flask session + browser localStorage.
- **Prompt engineering**
  - Dynamic persona with memory context injection.
- **Tool routing strategy**
  - Deterministic command handling for high-confidence tasks.
- **Robust error handling**
  - Defensive checks for malformed LLM responses and API failures.
- **JSON-first API contracts**
  - Tool responses consistently structured for frontend rendering.

### Most technically challenging part and solution
The most challenging part is balancing:
- persona consistency,
- long-term memory,
- and reliable tool behavior.

Solution:
- Keep high-risk tasks deterministic (tool functions).
- Keep conversational flexibility in LLM path.
- Persist user memory in DB and inject into system prompt every turn.
- Run extraction substeps (profile/topics) after each response to keep memory current.

---

## 4. Code Structure Walkthrough

### Main project files
- `app2.py`
  - Core backend app.
  - Defines DB model (`UserMemory`), memory pipeline, prompt assembly, chat/tool routes, startup logic.
- `tools.py`
  - Utility toolkit:
    - `get_security_news()`
    - `analyze_password_strength()`
    - `check_password_breach()`
    - `get_surveillance_camera()`
    - `google_dorking_search()`

### Frontend files
- `templates/index.html`
  - Main UI skeleton for chat interface.
- `static/script.js`
  - Command detection, request flow, chat rendering, loading states, masked password display, command suggestions.
- `static/style.css`
  - Matrix UI theme, chat layout, input mirror layer, command suggestion dropdown, visual effects.

### Deployment files
- `pi_setup/DEPLOY.md`
  - Installation and troubleshooting guide for Raspberry Pi deployment.
- `pi_setup/wasp_bot.service`
  - Backend service definition for auto-start and restart policy.
- `pi_setup/wasp-bot-browser.sh`
  - Browser startup script with readiness check.
- `pi_setup/wasp_bot_browser.desktop`
  - Desktop autostart entry.

### Additional folders/files
- `matrix-page/`
  - Legacy or prototype matrix chat UI.
- `requirements.txt`
  - Runtime dependency list.
- `pyproject.toml`, `poetry.lock`
  - Poetry metadata/dependency setup.
- `facts.csv`, `facts.db`
  - Additional data artifacts in the repository.

---

## 5. Learning Outcomes

By building or studying this project, a developer learns how to:
- design and ship a full-stack AI application, not only a model call;
- implement persistent conversational memory with a relational DB;
- integrate external APIs safely and present tool outputs in a UX-friendly way;
- structure backend code for mixed flows (tool commands + free chat);
- maintain character/persona consistency with prompt engineering and context design;
- deploy a Python web app to Raspberry Pi with auto-start and kiosk browser behavior.

### What a junior developer would gain
- Practical Flask API architecture.
- Real-world request/response and error-handling patterns.
- Frontend-backend integration using fetch and structured JSON.
- Confidence with environment variables and secret management basics.
- Understanding of production concerns (service startup order, recovery, logs).

---

## 6. End-to-End Data Flow (How it all fits together)

1. User enters text in the web UI.
2. `static/script.js` classifies command type or normal chat.
3. Browser sends request to Flask endpoint:
   - `/chat` for normal chat and OSINT command,
   - `/check-password`, `/security-news`, `/surveillance` for dedicated tools.
4. Backend (`app2.py`) resolves user identity via session/localStorage payload.
5. For normal chat:
   - load memory from SQLite,
   - build system prompt with memory context,
   - call Claude API (with optional web search tool capability),
   - parse final response text.
6. Memory update pipeline runs:
   - profile extraction,
   - topic summary extraction,
   - append user and assistant messages to recent history.
7. Response is returned as JSON to frontend.
8. Frontend renders response in terminal-style chat, handles special formatting for tool outputs.

---

## Short technical assessment

This is a strong educational full-stack AI project because it demonstrates:
- AI orchestration (prompt + memory + tools),
- API and DB design,
- frontend UX design,
- and deployment automation in one integrated system.
