Theory
Evidence-grounded Bull, Bear, and Judge debate workflows for inspectable market analysis.
Live application · API health check
Theory is a deployed full-stack application for exploring a market-research question through a persisted, multi-agent reasoning cycle. Rather than returning an opaque one-shot answer, Theory creates a ticker-scoped session, records the structured state and reasoning artifacts produced during each step, and surfaces the result as an inspectable workspace.
A user can launch a security workspace, inspect the current world state and prior reasoning, run the next debate step, and review the resulting actions, claims, controls, memory, quality metrics, and latest Judge verdict. The UI refreshes from persisted session state after a completed step, so results appear without a manual browser reload.
Why Theory
Market analysis often collapses evidence, assumptions, counterarguments, and conclusions into one untraceable response. Theory treats a reasoning cycle as application state instead:
Session-scoped: analysis is tied to a durable ticker-specific session.
Inspectable: the workspace exposes actions, claims, runtime controls, quality metrics, and memory rather than only a final conclusion.
Adversarial by design: Bull/thesis and Bear/risk perspectives are represented as distinct reasoning roles before Judge synthesis.
Evidence-aware: world-state and evidence services supply structured context for the debate workflow.
Refresh-safe: a completed next-step response triggers a Next.js route refresh that re-reads persisted session detail.
Theory is a portfolio application for demonstrating full-stack, applied-AI systems design. It is not investment advice and should not be used as the sole basis for trading or investment decisions.
Live demo
Open theory-app.fly.dev and launch a workspace for a supported ticker.
In a session workspace, use Run next step to advance the reasoning cycle. The application records the completed step and refreshes the session view to show the updated artifacts.
Architecture
flowchart LR
    U[Researcher] --> UI[Theory App<br/>Next.js · React · TypeScript]

    UI -->|Create session<br/>Run next step<br/>Read session detail| API[Theory API<br/>FastAPI]

    API --> ORCH[Session orchestration]
    ORCH --> WS[World-state builder]
    ORCH --> EV[Evidence mapping<br/>and evidence packets]

    EV --> BULL[Thesis / Bull agent]
    EV --> BEAR[Risk / Bear agent]
    BULL --> JUDGE[Judge agent]
    BEAR --> JUDGE

    ORCH --> CTRL[Grounding · calibration<br/>contradiction controls]
    JUDGE --> MEM[Session / Judge memory]

    WS --> DB[(PostgreSQL<br/>sessions · world state · evidence<br/>actions · claims · controls · memory)]
    EV --> DB
    BULL --> DB
    BEAR --> DB
    JUDGE --> DB
    CTRL --> DB
    MEM --> DB

    UI -->|router.refresh after<br/>completed step| API

    classDef client fill:#1d4ed8,color:#ffffff,stroke:#1e3a8a;
    classDef service fill:#0f766e,color:#ffffff,stroke:#134e4a;
    classDef agent fill:#b45309,color:#ffffff,stroke:#78350f;
    classDef store fill:#7c3aed,color:#ffffff,stroke:#4c1d95;

    class U,UI client;
    class API,ORCH,WS,EV,CTRL,MEM service;
    class BULL,BEAR,JUDGE agent;
    class DB store;
Researcher

Theory App
Next.js · React · TypeScript

Theory API
FastAPI

Session orchestration

World-state builder

Evidence mapping
and evidence packets

Thesis / Bull agent

Risk / Bear agent

Judge agent

Grounding · calibration
contradiction controls

Session / Judge memory

PostgreSQL
sessions · world state · evidence
actions · claims · controls · memory

Create session
Run next step
Read session detail

router.refresh after
completed step

​
Request lifecycle
sequenceDiagram
    autonumber
    participant R as Researcher
    participant UI as Next.js UI
    participant API as FastAPI API
    participant S as Session services
    participant D as PostgreSQL

    R->>UI: Launch ticker workspace
    UI->>API: POST /sessions
    API->>S: Bootstrap session and world state
    S->>D: Persist session state
    API-->>UI: session_id and initial state

    R->>UI: Run next step
    UI->>API: POST /sessions/{sessionId}/step
    API->>S: Build evidence packet and execute debate step
    S->>S: Thesis/Bull, Risk/Bear, and Judge reasoning
    S->>D: Persist action, claim, controls, memory, and verdict
    API-->>UI: step_status = completed

    UI->>UI: router.refresh()
    UI->>API: GET /sessions/{sessionId}
    API->>D: Read current persisted session detail
    API-->>UI: Updated actions, claims, metrics, and memory
    UI-->>R: Render refreshed workspace
PostgreSQL
Session services
FastAPI API
Next.js UI
Researcher
PostgreSQL
Session services
FastAPI API
Next.js UI
Researcher
Launch ticker workspace
1
POST /sessions
2
Bootstrap session and world state
3
Persist session state
4
session_id and initial state
5
Run next step
6
POST /sessions/{sessionId}/step
7
Build evidence packet and execute debate step
8
Thesis/Bull, Risk/Bear, and Judge reasoning
9
Persist action, claim, controls, memory, and verdict
10
step_status = completed
11
router.refresh()
12
GET /sessions/{sessionId}
13
Read current persisted session detail
14
Updated actions, claims, metrics, and memory
15
Render refreshed workspace
16
​
What the workspace shows
Surface
Purpose
World state
Structured ticker context spanning market, fundamental, event, and peer state
Actions
Recorded agent actions and rationale from reasoning steps
Claims
Bull/Bear-oriented claims, confidence, status, and linked evidence IDs
Latest Judge verdict
The most recent Judge-oriented synthesis captured in session memory
Memory timeline
Persisted episodic history associated with the session
Quality metrics
Debate-quality, evidence-diversity, repetition-risk, and Judge-check signals
Controls
Runtime configuration and control state exposed for inspection
Technical design
Persisted debate state
Theory models a debate as durable application state rather than transient chat text. The session detail response brings together:
Session metadata and mode
World state for the selected security
Evidence items
Agent actions and claims
Runtime controls
Episodic memory and Judge memory summaries
Quality metrics
This design makes the application easier to inspect, debug, and extend because the UI renders a persisted view of what happened during the reasoning process.
Distinct reasoning roles
The API organizes the debate workflow around specialized services:
Planner: coordinates the next step in a session.
Thesis/Bull perspective: develops a favorable or supporting thesis.
Risk/Bear perspective: introduces downside, counterarguments, and risk framing.
Judge: synthesizes the step into a verdict-oriented memory artifact.
The application also includes control-oriented services for grounding, calibration, and contradiction handling, which keep these concerns explicit rather than burying them inside a single prompt or UI response.
Fresh state after a completed step
The session-step endpoint returns a completed response only after the relevant step has been processed and persisted. On success, the Next.js client invokes router.refresh(), which re-renders the session route and reads the current GET /sessions/{sessionId} detail response.
This keeps the interaction simple and reliable for the current synchronous step workflow:
POST /sessions/{sessionId}/step
→ completed response
→ router.refresh()
→ GET /sessions/{sessionId}
→ updated session workspace
​
Technology stack
Layer
Technology
Frontend
Next.js 16, React 19, TypeScript, CSS Modules, clsx
Backend
Python 3.14+, FastAPI, Pydantic
Data access
SQLAlchemy async support, asyncpg
Database design
PostgreSQL schemas for core state, memory, debate, controls, and evaluation
External-service clients
OpenAI SDK and HTTPX
Deployment
Fly.io: separate frontend and API applications
Testing
Pytest and pytest-asyncio
Repository layout
Theory/
├── logos-mind/app/api/src/
│   ├── core_api/
│   │   ├── routes/              # Health, sessions, securities, evaluations
│   │   ├── services/
│   │   │   ├── agents/          # Planner, thesis, risk, Judge roles
│   │   │   ├── control/         # Grounding, calibration, contradictions
│   │   │   ├── debate/          # Evidence packets
│   │   │   ├── evidence/        # Evidence mapping
│   │   │   ├── memory/          # Episodic and semantic memory services
│   │   │   ├── session/         # Bootstrap and Judge-memory handling
│   │   │   ├── storage/         # PostgreSQL and cache integrations
│   │   │   └── world_state/     # Market, fundamental, event, and peer features
│   │   ├── db/                  # ORM/session configuration
│   │   └── repositories/        # Session persistence
│   └── main.py                  # FastAPI application entry point
├── pathos-ui/
│   ├── app/                     # Next.js routes and pages
│   ├── components/              # Workspace and session UI components
│   └── lib/                     # API client and TypeScript contracts
├── sql/postgres/                # Core, memory, debate, control, evaluation schemas
├── Dockerfile                   # API container image
├── fly.toml                     # theory-api deployment configuration
└── pyproject.toml               # Python project and dependency definition
​
Local development
Prerequisites
Python 3.14+
Node.js compatible with Next.js 16
PostgreSQL instance configured for the API
Required API credentials and configuration values in a local environment file
Never commit .env files, database credentials, or third-party API keys.
1. Configure the API
From the repository root, create a local environment file from the template:
cp env.example .env
​
Fill in the values required by your environment. Refer to env.example and the API configuration module for the authoritative list of variables.
Install Python dependencies:
uv sync
​
If you use a conventional virtual environment instead of uv, install from the project dependency configuration in the manner appropriate for your environment.
Apply the PostgreSQL schema files in the project’s intended order before starting the API. The repository contains modular SQL definitions under sql/postgres/ for extensions, core tables, memory, debate state, controls, and evaluation.
Start the API from the repository root:
uv run uvicorn main:app --app-dir logos-mind/app/api/src --reload --host 0.0.0.0 --port 8000
​
Verify it is reachable:
curl <http://127.0.0.1:8000/health>
​
2. Configure and run the UI
In a second terminal:
cd pathos-ui
npm install
​
Create a local UI environment file if needed:
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000/
​
Then start the application:
npm run dev
​
Open http://localhost:3000.
3. Run checks
Backend tests:
uv run pytest
​
Frontend linting and production build:
cd pathos-ui
npm run lint
npm run build
​
A production build is an important validation step because it runs the stricter TypeScript checks that can expose drift between API response contracts and the UI’s typed data model.
Deployment
Theory is deployed as two Fly.io applications:
Service
Fly app
Responsibility
Web application
theory-app
Next.js user interface
API
theory-api
FastAPI session, reasoning, and persistence API
API
From the repository root:
fly deploy
​
The API Fly configuration uses:
theory-api as the application name
Dallas/Fort Worth (dfw) as the primary region
GET /health as the HTTP health check
Fly Machine auto-start and auto-stop settings for idle capacity
Frontend
From pathos-ui/:
fly deploy
​
The frontend build is configured with the deployed API URL. Because values prefixed with NEXT_PUBLIC_ are exposed to browser code and included in the client build, ensure the public API base URL is correct before building and deploying the frontend.
API surface
The frontend currently relies on a session-oriented API shape:
POST /sessions
GET  /sessions
GET  /sessions/{sessionId}
POST /sessions/{sessionId}/step
GET  /health
​
The canonical schemas and route behavior live in the FastAPI route and Pydantic model modules. Treat those source definitions as authoritative when extending the product.
Engineering notes
Typed boundaries matter. The UI uses TypeScript contracts for session detail, list items, actions, claims, memory, quality metrics, and step responses. Aligning those contracts with actual API payloads prevents runtime ambiguity from leaking into the UI.
Persist first, render second. The session page renders durable state returned by the API, rather than relying on a client-only optimistic reconstruction of debate output.
Avoid stale server-rendered views. The session route uses dynamic rendering and uncached session reads so router.refresh() retrieves current persisted state after a completed step.
Keep the product claim honest. Theory demonstrates an inspectable market-analysis workflow. It does not provide investment advice or guarantee factual completeness, forecast accuracy, or trading performance.
Roadmap
Potential next steps, deliberately separate from the implemented workflow, include:
Richer evidence provenance and source-level inspection in the UI
Explicit session lifecycle/status visualization
Evaluation dashboards for debate-quality trends across sessions
Authentication and per-user workspace isolation
More robust job orchestration if a future reasoning workflow becomes long-running or asynchronous
Expanded test coverage around API contracts, persistence transitions, and UI refresh behavior

License
No license is currently specified. Add a license file before accepting external contributions or distributing the project under defined reuse terms.