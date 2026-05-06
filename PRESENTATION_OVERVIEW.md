# AI-ALRO: Presentation Reference Guide

**Autonomous Logistics & Routing Optimizer**
*High-level overview for demo Q&A*

---

## What Is This?

AI-ALRO is an AI-powered delivery routing system that demonstrates how multiple AI agents can collaborate to make decisions — and show their reasoning in real time. The focus is not just on *what* the AI decides, but *why*, so that a human operator can understand and trust the outcome.

Think of it like two AI advisors working simultaneously on the same problem:
- One advisor crunches numbers and ranks options by score
- The other reads the numbers and thinks out loud about whether they make sense
- Both advisors present their conclusions side by side, and the system surfaces any disagreement

---

## The Problem It Solves

When AI systems make decisions in high-stakes domains like logistics, operators often can't understand *why* a particular route was chosen. A system that says "take Route A" without explanation will be ignored — or blindly followed, which is worse. AI-ALRO makes the decision-making process visible and auditable.

---

## How It Works — Three Phases

### Phase 1: Signal Population
The system receives a delivery order and enriches it with real-world data:
- Which warehouses have stock and are nearby?
- Which drivers are available and how far away?
- What is the delivery zone's reliability history (complaint rates, success rates)?

Eight "signals" are populated and animated onto the screen, giving the operator a picture of the logistics context before any decision is made.

### Phase 2: Parallel Deliberation
Two AI agents evaluate the order simultaneously, shown side by side:

**Left panel — Optimizer Agent:**
Scores each routing option using a reward function with four components:
- Timeliness (will it arrive within the time window?)
- Cost efficiency (how much does it cost relative to the ceiling?)
- Proximity (how far is the warehouse and driver from the destination?)
- Zone risk penalty (deducted if the delivery zone has poor historical performance)

The top-ranked option is highlighted. All score breakdowns are visible.

**Right panel — Reasoner Agent:**
An LLM (Claude by default) reads the same data and audits the Optimizer's choice by thinking through:
1. What is driving the top score?
2. Is the ranking close or a clear winner?
3. Does this route unfairly avoid certain geographic zones?
4. What can the reward function *not* see? (driver familiarity, cargo type risk, etc.)

The reasoning streams token by token in real time — the operator watches the AI think, not just read a conclusion.

An **agreement indicator** shows whether both agents are converging or diverging as the reasoning develops.

### Phase 3: Resolution
The system compares both agents' conclusions and produces one of three outcomes:

| Outcome | Meaning |
|---|---|
| **Convergence** | Both agents agree. Decision confirmed. |
| **Qualification** | Optimizer's choice is correct, but Reasoner flags a risk the score can't capture (e.g., zone reliability issues). |
| **Override** | Reasoner recommends a different option due to fairness concerns or hidden risks the reward function misses. |

The final decision is shown with full attribution — which agent said what, and why.

---

## The Three Demo Scenarios

All three scenarios are pre-engineered to reliably trigger each resolution state:

| Scenario | Location | Resolution | What It Demonstrates |
|---|---|---|---|
| **1** | Union Square, SF | Convergence | Clean case — both agents agree on a clear winner |
| **2** | Oakland | Qualification | Score is right, but zone risk flags a condition the numbers can't see |
| **3** | Hayward | Override | Fairness constraint fires — routing pattern would deprive an underserved zone of service |

---

## The Tech Stack

### Frontend
- **React** (JavaScript UI framework) running on port 3000
- **Leaflet** for interactive map with real road-based route geometry
- Connects to backend via REST and Server-Sent Events (SSE) for streaming

### Backend (Four Microservices)
All services are Python with FastAPI:

| Service | Port | Role |
|---|---|---|
| **ERP Service** | 8001 | Provides warehouse, driver, and zone data |
| **Intake Agent** | 8002 | Enriches orders with ERP data; builds feature vectors |
| **Optimizer Agent** | 8003 | Scores routing options using reward function |
| **Reasoner Agent** | 8004 | Calls LLM, streams chain-of-thought, produces resolution |

### AI / LLM
- **Default**: Anthropic Claude (claude-sonnet-4-6)
- **Alternatives**: OpenAI GPT-4o, or local Ollama (self-hosted, no API key needed)
- LLM is called by the Reasoner Agent only; the Optimizer is pure math
- Temperature is set to 0 for reproducible, consistent reasoning output

### Infrastructure
- **Docker Compose** orchestrates all five services (4 backend + 1 frontend)
- Services communicate over an internal Docker network
- Health checks ensure services are ready before accepting traffic

---

## Key Design Decisions (For Technical Questions)

**Why two agents instead of one?**
Separating optimization (math) from reasoning (language) lets each agent do what it's best at. The Optimizer is fast and consistent; the Reasoner can surface context the reward function can't quantify (zone equity, driver familiarity, cargo risk).

**Why stream the reasoning token by token?**
Showing the reasoning as it forms — rather than displaying a finished paragraph — makes the deliberation feel real. The operator can see when the AI hesitates or qualifies a conclusion, not just the final output.

**What is the fairness constraint?**
The Reasoner's prompt explicitly instructs it to check whether the chosen route creates "geographic service deprivation" — i.e., whether cost optimization causes a zone with already-poor delivery service to be deprioritized further. Zones with <88% delivery success or >10% complaint rates are flagged as at-risk. This can trigger an Override.

**Is the Optimizer a real machine learning model?**
The Optimizer is a calibrated reward function (not a trained RL policy) for this demo. The architecture supports dropping in a trained policy later — the interface between components doesn't change. This is called out transparently in the project.

**What if the LLM is unavailable?**
The system degrades gracefully. The Reasoner falls back to the Optimizer's output alone, and the UI displays a visible "degraded mode" banner. No cascading failures.

**Why mock ERP data?**
The ERP service mimics a real warehouse management system with a REST interface. Swapping in a real ERP connector (SAP, Oracle WMS, etc.) requires only changing the data source behind the same API contract.

---

## Data Flow (Simplified)

```
User selects scenario
        ↓
Intake Agent enriches the order (calls ERP for warehouses, drivers, zones)
        ↓
Optimizer Agent scores all route combinations → returns ranked list
        ↓
Reasoner Agent streams chain-of-thought via SSE → produces conclusion
        ↓
Resolution Layer compares both → convergence / qualification / override
        ↓
Frontend renders all three phases with animations and live map
```

---

## Folder Structure (High Level)

```
ai-alro/
├── backend/
│   ├── erp_service/        ← Mock warehouse/driver/zone data
│   ├── intake_agent/       ← Order enrichment
│   ├── optimizer_agent/    ← Reward function scoring
│   ├── reasoner_agent/     ← LLM deliberation + resolution logic
│   │   ├── prompts.py      ← Chain-of-thought prompt engineering
│   │   ├── resolution.py   ← Convergence/qualification/override logic
│   │   └── demo_scenarios.py ← Pre-seeded scenario data
│   └── shared/
│       ├── models.py       ← Shared data models (Pydantic)
│       └── utils.py        ← Distance calculations, zone classification
│
├── frontend/
│   └── src/
│       ├── App.jsx                    ← Main layout
│       ├── hooks/useDeliberation.js   ← State machine orchestrating all phases
│       └── components/
│           ├── Phase1_Signals.jsx     ← Signal reveal animation
│           ├── Phase2_Deliberation.jsx ← Optimizer + Reasoner panels
│           ├── Phase3_Resolution.jsx  ← Final decision display
│           └── RouteMap.jsx           ← Leaflet map
│
├── docker-compose.yml      ← Runs all 5 services together
└── CONCEPT.md              ← Academic thesis + architecture doc
```

---

## One-Sentence Answers to Common Questions

**What does this do?**
It routes delivery orders using two AI agents that work in parallel — one optimizes by score, one reasons in plain language — and the operator watches both deliberate in real time.

**What's the AI doing?**
The Optimizer ranks routes using a weighted scoring function; the Reasoner uses a large language model (Claude) to audit that choice by thinking through fairness, risk, and edge cases.

**What's novel about it?**
Most AI systems show you a decision. This one shows you the deliberation — including when two agents disagree, and why.

**How was it built?**
Python microservices (FastAPI) for the backend, React for the frontend, Docker Compose for deployment, and Anthropic Claude as the LLM provider.

**Can it handle real data?**
The architecture is production-compatible. The ERP service is a mock, but the REST interface is the same one you'd use with a real warehouse system. The Optimizer can be upgraded to a trained RL policy without changing the surrounding system.

**What happens if the AI fails?**
If the LLM is unavailable, the system falls back to the Optimizer's output alone and shows a visible warning. No crashes, no silent failures.
