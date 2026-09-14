Theory

A full-stack, agentic market-reasoning workspace for investigating a public security through a structured world state, evidence ingestion, competing thesis formation, risk review, judge evaluation, and persistent session memory.

Rather than returning a single opaque recommendation, Theory makes the reasoning loop inspectable. Each session records the evidence available to the system, the actions taken by specialized agents, the claims they produce, control checks, judge summaries, and a timeline of memory episodes.
What it does

Theory turns a ticker into an auditable debate workspace:

    Builds a world state for a selected security.

    Ingests evidence from market and news/fundamental data sources.

    Runs an agent loop consisting of planner, risk, and judge steps.

    Persists session state in Postgres so prior investigations can be reopened.

    Displays evidence, actions, claims, controls, quality metrics, and memory in a Next.js workspace.

    Lists prior sessions on the home page, enabling users to return to and continue earlier reasoning runs.

The goal is not to present financial advice or a trading signal. It is to provide a transparent environment for examining how an agentic system forms, challenges, and evaluates an investment thesis.
Core workflow

text
Ticker
  ↓
World-state construction
  ↓
Evidence ingestion
  ↓
Planner step → thesis/action
  ↓
Risk step → challenge/counterclaim
  ↓
Judge step → evaluation + control checks + memory summary
  ↓
Persisted session timeline and quality metrics

A session follows a repeating three-step loop:
Step	Agent	Responsibility
1	Planner	Produces an evidence-grounded action and, when appropriate, a thesis or claim.
2	Risk agent	Reviews the available context, challenges the latest thesis, and surfaces countervailing risks.
3	Judge agent	Evaluates recent debate context, writes control checks, and records a judge-summary memory episode.
Features

    Structured world state

        Captures a security reference plus market, fundamental, event, and peer context.

        Persists snapshots so each session has a stable, inspectable context.

    Evidence ingestion

        Converts source news into normalized evidence records.

        Stores source metadata, timestamps, summaries, payloads, freshness scores, and confidence values.

    Multi-agent debate loop

        Planner, risk, and judge services execute in predictable round-robin order.

        Each step is persisted as an action, with optional claims and control checks.

    Claims and actions

        Tracks bull/bear claims, agent rationale, confidence, evidence IDs, round number, and status.

        Keeps the debate history visible rather than compressing it into an unexplained final answer.

    Judge controls and quality metrics

        Records checks such as evidence distinctness, contradiction quality, and unsupported repetition.

        Summarizes debate quality, evidence diversity, repetition risk, and judge-check counts.

    Session memory timeline

        Persists ingestion, world-state, and judge-summary episodes.

        Renders a chronological timeline so users can inspect how reasoning evolved over the course of a session.

    Previous sessions

        Displays recent persisted sessions on the home page.

        Shows ticker, mode, timestamps, and counts for actions, claims, and memory episodes.

        Lets users return directly to prior session workspaces.

    Developer visibility without overwhelming the product UI

        World state and control summaries are presented in readable cards.

        Full raw payloads remain available through a collapsible developer view.

Architecture

text
theory/
├── logos/                         # FastAPI application
│   ├── core_api/
│   │   ├── routes/                  # HTTP routes, including session APIs
│   │   ├── models/                  # Pydantic API and domain models
│   │   └── services/                # World state, evidence, and agent services
│   ├── repositories/                # Async SQLAlchemy data access layer
│   └── db/                          # Database session and ORM models
│
└── pathos/                        # Next.js application
    ├── app/ or client-workspace/    # Workspace routes and pages
    ├── components/                  # Session UI components
    └── lib/                         # API client and TypeScript contracts

Backend

The backend is built around FastAPI, async SQLAlchemy, and PostgreSQL.

Key responsibilities:

    create and retrieve persisted security sessions

    create world-state snapshots

    ingest and persist evidence

    execute planner, risk, and judge workflow steps

    persist actions, claims, control checks, and memory episodes

    expose concise session summaries for the frontend home page

Frontend

The frontend is a Next.js workspace focused on legibility and traceability.

Key views include:

    a homepage for launching ticker analysis and reopening recent sessions

    a security workspace for beginning analysis on a selected ticker

    a persisted session page with quality metrics, world state, actions, claims, controls, latest judge verdict, and session memory timeline

API surface

The session API is organized around the /api/v1/sessions resource.
Method	Route	Purpose
POST	/api/v1/sessions	Creates a new analysis session for a ticker.
GET	/api/v1/sessions	Returns recent session summaries for the homepage.
GET	/api/v1/sessions/{session_id}	Returns the full persisted session detail.
POST	/api/v1/sessions/{session_id}/step	Executes the next planner, risk, or judge step.
Session list response

The home-page list endpoint returns compact session metadata instead of full detail payloads:

json
{
  "sessions": [
    {
      "session_id": "c2c0d20f-8ae0-4ea8-b4f4-188d9f2f91bf",
      "ticker": "NVDA",
      "mode": "debate",
      "status": "created",
      "created_at": "2026-07-02T16:00:00Z",
      "updated_at": "2026-07-02T16:04:00Z",
      "total_actions": 3,
      "total_claims": 3,
      "total_episodes": 4
    }
  ]
}

Local development
Prerequisites

    Python 3.11+ recommended

    Node.js 20+ recommended

    PostgreSQL

    npm, pnpm, or your preferred Node package manager

    Market-data provider credentials, if required by your environment

1. Configure the backend

From the backend directory, create an environment file appropriate for your configuration. At minimum, the application needs a PostgreSQL connection string and any third-party provider credentials used by the world-state/evidence services.

Example:

bash
cd backend

export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/theory"
export MASSIVE_API_KEY="your_provider_key"

Run database migrations or create the schema using the migration/setup workflow configured in this repository.

Start the FastAPI development server using the project entry point. For example:

bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000

The API should then be available at:

text
http://127.0.0.1:8000/api/v1

    Adjust main:app if this repository uses a different ASGI module path.

2. Configure the frontend

In a second terminal:

bash
cd frontend
npm install

Create .env.local:

bash
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000/api/v1

Start the Next.js development server:

bash
npm run dev

Open the local workspace at the URL printed by Next.js, commonly:

text
http://localhost:3000

Typical usage

    Open the workspace home page.

    Enter a ticker, or choose a demo security.

    Create a new persisted session.

    Inspect the world state and initial evidence.

    Run the next step to advance the planner → risk → judge loop.

    Review generated actions, claims, controls, quality metrics, and the latest judge verdict.

    Return to the homepage later and reopen the session from Recent sessions.

Environment variables
Variable	Used by	Purpose
DATABASE_URL	Backend	Async PostgreSQL connection string.
MASSIVE_API_KEY	Backend	Credentials for the configured market/news data provider.
NEXT_PUBLIC_API_BASE	Frontend	Public base URL for the FastAPI API, including /api/v1.

Do not commit secret values to version control. Use local environment files during development and platform-managed secrets in production.
Deploying to Fly.io

This repository is structured as a monorepo, with the backend and frontend deployed as separate Fly apps.

text
theory/
├── logos/   → theory-api
└── pathos/  → theory-web

A practical Fly deployment layout is:

    theory-api: FastAPI backend

    theory-web: Next.js frontend

    theory-db: Fly Postgres cluster attached to the backend

Deployment outline

    Launch the API app from backend/.

    Create a Fly Postgres cluster.

    Attach the database to the API app so Fly supplies DATABASE_URL as an app secret.

    Set backend provider/API-key secrets.

    Deploy the backend and verify its health endpoint/API routes.

    Launch the web app from frontend/.

    Set the frontend API base URL to the deployed backend URL.

    Deploy the frontend.

Example commands:

bash
# Backend
cd backend
fly launch --name theory-api --no-deploy

# Database
fly postgres create --name theory-db
fly postgres attach theory-db --app theory-api

# Backend secrets
fly secrets set MASSIVE_API_KEY="your_provider_key" --app market-intelligence-api

# Deploy backend
fly deploy

# Frontend
cd ../frontend
fly launch --name theory-web --no-deploy
fly secrets set NEXT_PUBLIC_API_BASE="https://theory-api.fly.dev/api/v1" --app theory-web
fly deploy

Fly deployments use container images. You do not need to make Docker part of your everyday local workflow, but each deployable service will normally need deployment configuration such as a Dockerfile and fly.toml generated or maintained within its own directory.
Important implementation notes

    Session summaries should use the lightweight GET /sessions API instead of fetching full session detail for every item on the homepage.

    Session detail pages should tolerate missing updated_at values by falling back to created_at.

    The frontend should treat NEXT_PUBLIC_API_BASE as public configuration; database credentials must remain backend-only.

    The agent output is an exploratory reasoning artifact, not investment research, trading advice, or a guarantee of performance.

Roadmap

Potential next improvements:

    Dedicated all-sessions page with pagination, filtering, and search.

    Session deletion and archival controls.

    Richer evidence-source attribution and evidence provenance links.

    Filterable agent-turn timeline and round-by-round comparison.

    Background jobs for long-running ingestion or enrichment workflows.

    Authentication and user-scoped sessions.

    Automated database migrations as part of the deployment release process.

    Test coverage for repository aggregation queries and session API contracts.

Disclaimer

Theory is an experimental software project for exploring structured, agent-assisted market reasoning. It does not provide investment advice, financial advice, trading recommendations, or guarantees of future results. Verify all information independently and consult qualified professionals before making financial decisions.