# AI DLC (Agentic AI SDLC): Understanding and Assessment

**Prepared:** 20 November 2026
**Sources reviewed** (copies are in [sources/](sources/)):
- `AI_DLC_Conversation_Export.md`: the ChatGPT learning conversation (cloud options, SDLC phases, orchestration, brownfield context, GCP training)
- `Autonomous_SDLC.pptx`: the 5-slide deck (AI in the SDLC, Capability Map, MVP Autonomy Ladder, GCP Target Architecture, 12-week Roadmap)

---

## 1. What AI DLC is, in one paragraph

AI DLC is ITMC's plan for an **agent-run software delivery lifecycle**. Specialist AI agents do the work in all seven SDLC phases (Requirements → Design → Development → Review & CI → Testing → Release → Operate). A **named human approves at every gate**, and no agent merges or ships on its own. The system is a **thin orchestration layer on top of existing tools** (Jira, Git, CI/CD, observability), so it is a **brownfield** design. Development is the MVP. Its agent earns autonomy step by step over 12 weeks, moving from chores to bugs to small features to medium features, and it only moves up when measured gates hold. The deck targets **Google Cloud**. The meeting itself had not yet chosen between Azure and GCP.

---

## 2. What the presentation actually says (slide by slide)

### Slide 1: AI in the SDLC
Seven phases. Each is labelled **"Autonomous"** and has an AI-does list and a human gate. The operating principle: *agents do the work in every phase; a named human approves at each gate, starting with every merge.* The conversation's section 7 covers this slide accurately.

### Slide 2: Capability Map (not covered in the conversation)
This is the slide that turns the idea into something measurable. Each phase has a success metric:

| Phase | AI feature | Human gate | Success metric |
|---|---|---|---|
| Requirements | Turns requests and **call notes** into stories and acceptance criteria; asks on the ticket when unclear | PM / BA | Time to refined backlog |
| Design | Design docs, ADRs, threat model from a problem statement and the existing architecture | Architect | Design review cycle time |
| Development | Agent-ready ticket → tested PR in a sandbox, climbing the ladder | Human approves PR; **agent cannot merge** | PR acceptance 60–70%; cost per merged PR |
| Review & CI | Independent reviewer agent on every PR; **sends fixes back to the dev agent** | Human reviewer still required | Review turnaround; escaped defects |
| Testing | Generates and maintains unit/API tests and synthetic data; triages **and fixes** flaky tests | QA / dev | Coverage on new code; test upkeep effort |
| Release | Notes, change-risk score, staging deploy and checks | Release manager | Release prep time; change failure rate |
| Operate | Alert/incident triage, diagnosis, fix PRs, approved runbooks | On-call | MTTR; alert-to-diagnosis time |

Several of these are DORA-style metrics (change failure rate, MTTR). They only mean something if we **baseline them before the agents go live**, which is why the roadmap has "baselines" in weeks 1–2.

### Slide 3: MVP Autonomy Ladder (Development)
The conversation's section 11 matches the slide, with one omission: the Stage 1 gate also requires **"CI green first pass"**.

| Stage | Weeks | Scope | Gate to advance |
|---|---|---|---|
| 1 Chores | 2–4 | Dependency bumps, flaky tests, docs/lint | 80% merged without rework, CI green first pass, zero incidents |
| 2 Bugs | 5–6 | Bugs with a reproducible failing test | 70% acceptance; failing test goes green without breaking others |
| 3 Small features | 7–9 | Well-specified tickets, ~3-day class, must pass intake check | 60–70% acceptance; cost per merged PR tracked and stable |
| 4 Medium features | 10–12 | Agent decomposes work; parallel sub-agents; small sub-PRs; reviewer agent on each | 60%+ acceptance, zero agent-linked incidents, then widen to more repos |

Promotion rule: the gates must hold for about a week before moving up. If a gate is missed, the stage holds until it is fixed.

### Slide 4: GCP Target Architecture
Four layers plus human gates. The deck has more detail than the conversation's summary did:

- **Triggers:** Jira "agent-ready" label (Pub/Sub webhook), Git events (Eventarc), CI failure (Cloud Build), alerts (Cloud Monitoring), schedules (Cloud Scheduler).
- **Orchestration:** intake check → task planning → queue/routing → budget and retry limits → handoff when blocked. Runs on Cloud Run, Cloud Workflows, Cloud Tasks, with Firestore for run state.
- **Intelligence:**
  - *Context and knowledge*: repo context files, ADRs, API specs, ticket/wiki history, stored in BigQuery, Cloud Storage and vector search.
  - *Specialist agents*: Reqs, Design, Dev, Reviewer, Test, Release, Ops. Each runs in an isolated sandbox, and the Reviewer is separate from Dev. Built with ADK 2.0, Agent Platform, Cloud Run jobs and GKE Sandbox.
  - *Tools and connectors*: Git and CI/CD, Jira, observability, docs and MCP servers, Cloud Build/Deploy, Artifact Registry, Cloud Logging.
- **Platform:**
  - **Model gateway and cost caps: Model Garden (Claude, Gemini)** plus **Cloud Billing budgets**. The deck plans to use **both Claude and Gemini**. The conversation left this out.
  - **Sandbox with no prod access**: Agent Identity, GKE Sandbox, VPC Service Controls.
  - Governance and audit: Agent Gateway, IAM, Secret Manager, Cloud Audit Logs.
  - Metrics and evaluation: Cloud Monitoring, BigQuery, **Looker, Agent Platform evals**.
- **Human gates:** PR merge, architecture sign-off, production release, on-call actions.

### Slide 5: 12-week Roadmap (not covered in the conversation)
Week ranges below are read from where the bars sit on the slide:

| Workstream | Weeks |
|---|---|
| Foundations: governance, GCP landing zone, baselines | W1–W2 |
| Development ladder | Chores W2–4 → Bugs W5–6 → Small W7–9 → Medium W10–12 |
| Review & CI agent | Pilot repos W2–4 → All repos W5–12 |
| Testing agent | Generation and triage W3–6 → Expand coverage W7–12 |
| Requirements agent | Stories and criteria W5–8 |
| Design agent | Docs and threat model W6–9 |
| Release agent | Notes and staging deploy W8–10 |
| Operate agent | Triage and fix PRs W9–12 |

Months are framed as **1: Foundations + pilot**, **2: Extend**, **3: Scale**. The deck calls this pace **aggressive**.

---

## 3. How the conversation and the deck line up

| Topic | Conversation | Deck | Comment |
|---|---|---|---|
| 7 SDLC phases and gates | ✅ Covered with a leave-management example | ✅ | Consistent |
| Autonomy ladder | ✅ | ✅ | Conversation misses "CI green first pass" in Stage 1 |
| Capability map and metrics | ❌ | ✅ | **Gap**: metrics are how success will be judged |
| Roadmap | ❌ | ✅ | **Gap**: shows all 7 agents live within 12 weeks |
| Model choice | Vertex AI and Gemini | **Model Garden: Claude + Gemini** | Deck is already multi-model |
| Cloud choice | Undecided; keep it portable | **GCP only** | **Tension**: the deck assumes a decision the meeting didn't make |
| Greenfield vs brownfield | Open question | "Thin layer over your existing tools" | Deck answers it: **brownfield** |
| Brownfield context layer | ✅ Detailed (7 context types) | Repo context files, ADRs, specs, history | Consistent; the conversation goes deeper |
| Platform controls | Partial | Adds Cloud Billing budgets, Agent Identity, Looker, evals | Conversation summary is incomplete |
| Target users | Developers, **testers, data engineers** | Software SDLC only | **Gap**: no data-engineering use case |

---

## 4. My assessment

### What's strong
1. **Graduated autonomy with measurable gates.** Promotion depends on acceptance rate, rework, incidents and cost, not on a calendar date. This is the most defensible part of the plan.
2. **Humans keep the irreversible actions.** Merge, architecture sign-off, prod release and on-call actions all need a human, and agents have no prod access. That is the right risk posture for a first enterprise rollout.
3. **The reviewer agent is independent of the dev agent.** Separating the two reduces "grading your own homework".
4. **Brownfield-first.** Plugging into Jira, Git and CI that teams already use is much easier to adopt than a new platform.
5. **Cost is a first-class concern.** Budget and retry limits sit in the orchestrator, cost per merged PR is a gate metric, and there are billing budgets at the platform layer.

### Risks and inconsistencies to raise
1. **"Autonomous" is used loosely.** Every phase is labelled "Autonomous" while every phase also has a human gate. Leadership or clients may read this as "no human involvement". A better label is *"agent-executed, human-approved"*.
2. **"Every other phase climbs the same ladder" doesn't match the roadmap.** On slide 5, Requirements, Design, Release and Operate each get one 3–4 week bar. There is no time for them to climb four stages. Either they start and stay at stage 1 (draft or assist mode) within the 12 weeks, or they need their own ladder definitions and gates. Today only Development has one.
3. **The 12-week plan is very compressed.** A GCP landing zone, governance and metric baselines in two weeks is optimistic for an enterprise, where security reviews, VPC-SC and IAM approvals often take longer. Seven agents also go live in parallel while the Dev ladder is still being proven. The meeting's "first draft within about one month" (around 11 Dec 2026) is a **framework draft**, not working agents. It's worth making that distinction explicit.
4. **The cloud decision is assumed.** The deck is fully GCP. If Azure is still on the table, we either (a) show a provider-neutral reference architecture plus a GCP and an Azure mapping, or (b) get the GCP decision confirmed. The portability levers are the model gateway, MCP for tools, A2A for agent-to-agent, and keeping orchestration logic out of provider-specific workflow engines where practical.
5. **Ladder gates measured on small numbers.** "80% of PRs" over about two weeks of chores may cover only a handful of PRs. Define a **minimum PR count** for each gate, otherwise the percentages are noise.
6. **"Agent-ready" and the intake check are undefined.** Stages 3–4 depend on them. We need a written Definition of Ready: acceptance criteria present, scope estimate, linked repo, test strategy, no secrets or PII in the ticket.
7. **Security threats specific to agents are not called out.** Prompt injection through ticket text, PR comments, docs or dependency READMEs; supply-chain risk when agents bump dependencies; secrets leaking into model context; agents changing CI config or tests to make checks pass. These belong in the threat model and the reviewer agent's checklist.
8. **No evaluation step before going live.** "Agent Platform evals" is named but there's no offline eval set, such as historical tickets with known good PRs, to test agents *before* they touch real repos. This is cheap and lowers Stage 1 risk.
9. **Data engineers are missing.** The original goal included data engineers, but the deck has no pipeline, SQL or data-quality agent. Either add a use case (for example dbt/SQL test generation or pipeline failure triage) or state that it is out of scope for the MVP.
10. **Build vs buy is not addressed.** Off-the-shelf coding agents exist across vendors, including Google's own developer agents, GitHub Copilot's coding agent and Claude Code. The deck builds a custom orchestrator without saying why. The value of AI DLC is probably the **orchestration, gates, context layer and metrics**, not the coding agent itself. The framework could wrap a bought coding agent instead of building one.
11. **Client and code data governance.** For ITMC client repos: data residency, whether client code may be sent to which model provider, and contract or IP terms. This drives the Claude and Gemini model choices.

### Items to verify before quoting them externally
The conversation contains product and certification details that move fast and could not be checked from these sources. Confirm them on official Google and Microsoft pages before putting them in emails or slides:
- "ADK 2.0", "Agent Platform", "Agent Gateway", "Agent Identity" (exact product names and GA status)
- GEAR programme terms (e.g. "35 learning credits per month")
- Professional Agentic Architect exam details (duration, question count, $200 fee, lab component, validity)
- Claude availability in Vertex AI Model Garden for the target region

---

## 5. Suggested answers or positions for the open decisions

| Open decision | Suggested position |
|---|---|
| MVP capabilities | Dev agent through Ladder Stages 1–2, plus the Reviewer agent on pilot repos. Other phase agents start in "draft for human" mode. |
| Greenfield vs brownfield | Brownfield (the deck already assumes it). Pick 1–2 pilot repos with good test coverage. |
| Cloud | Present GCP as the reference implementation and add a one-page Azure mapping (Foundry/Azure OpenAI, Container Apps/AKS, Durable Functions/Logic Apps, AI Search, Key Vault, Monitor). |
| Multi-model | Yes, through the model gateway. The deck already lists Claude and Gemini. |
| Orchestration | ADK-based orchestrator on Cloud Run, with state in Firestore. Keep workflow logic portable. |
| Initial agents | Dev, Reviewer, Test (these are the ones that affect the MVP gates). |
| Context layer | Repo context file per repo (conventions, build/test commands), plus an ADR/spec index, plus ticket history RAG. |
| Security | Sandbox with no prod access, a per-agent identity, least-privilege repo tokens, and an explicit prompt-injection threat model. |
| Gates and metrics | Add a minimum PR count per gate. Baseline DORA metrics in weeks 1–2. |
| Owners | One owner per layer (Orchestration, Intelligence/context, Agents, Platform/governance, Metrics). |
| Learning | GEAR paths: ADK → Vector Search/RAG → Deploy. Defer the certification until after hands-on work. |

---

## 6. Glossary (quick reference)

- **ADR**: Architecture Decision Record; a short document capturing one design decision and why.
- **Agent-ready ticket**: a ticket that passes the intake check and can be given to an agent.
- **Orchestrator**: coordinates agents, routing, state, retries, budgets and human handoff.
- **Blast radius**: how much breaks if a change goes wrong.
- **MTTR**: mean time to recovery. **Change failure rate**: share of deployments that cause a failure (both DORA metrics).
- **MCP / A2A**: Model Context Protocol (agent ↔ tools) and Agent-to-Agent protocol (agent ↔ agent).
- **VPC Service Controls**: GCP perimeter that stops data leaving defined services.
