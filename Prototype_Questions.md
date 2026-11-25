# GCP Prototype: Questions and Decisions

Status: **answers recorded. Nothing has been built or created yet.**

## What the meeting transcript (`sources/AI DLC framework.vtt`, date not in the file) established
- Cloud: Prachi leaned towards GCP ("maybe we choose GCP"). **Dipesh has since confirmed GCP is final.**
- Language focus: **Java**. The framework must handle both greenfield and brownfield.
- Brownfield approach: copy a **sample public repo to GitHub** and point the framework at it.
- Prachi's **Stage 1 is different from the deck**: requirements (user stories) from emails, call transcripts and recordings, plus an architecture diagram. The deck's Stage 1 is "chores".
- Requirements must say **where in the existing code** a change goes (agent searches the repo first).
- Context layer: GitHub, Jira, API specs, architecture diagrams. Code goes into vector search (RAG).
- Prachi: **BigQuery is probably not needed**; choose only the components that are required.
- Orchestration in Vertex AI, triggered from a **UI** or a chat/Teams message.
- Human approval at every stage, with feedback captured.
- Aryan: **context manager** between agents to save tokens.
- "Testing" = **unit testing**. End-to-end testing and data engineering are later, separate frameworks.
- Actions: GCP hands-on this week, **revise plan/dates by Friday**, next meeting **Wednesday**. Dates are fixed once given.

## Decisions (Dipesh's answers)

| # | Question | Answer |
|---|---|---|
| 1 | GCP project | ITMC company: **create a new, dedicated project** (Claude creates it with gcloud as itmcsystemsdigital@gmail.com, showing commands and billing account first) |
| 2 | Access | Owner / Editor |
| 3 | Budget | Set everything up while **minimising credit use**. Discuss spend before anything that bills meaningfully is actually used. |
| 4 | Region / data rule | No restriction |
| 5 | Local check | Done (see below) |
| 6 | Goal | **Both**: per-service demos, then one joined flow |
| 7 | Flow | **Requirements → user story** (Prachi's Stage 1) |
| 8 | Services | ADK + Agent Engine; Agent Garden + Model Garden; RAG/search services; Cloud Run + Firestore + Cloud Storage |
| 9 | RAG | **Compare** RAG Engine, Vertex AI Search and Vector Search on the same data |
| 10 | Models | **Gemini only** |
| 11 | Java repo | **spring-petclinic**, copied to **personal GitHub** |
| 12 | Sample input | **Real meeting transcript** for story generation **+ a short made-up PetClinic request** for the "where in the code" step |
| 13 | Ticketing | **Real Jira**: a new free Jira site. Dipesh is adding a Jira connector so Claude can create the sample tickets. |
| 14 | Interface | ADK web UI |
| 15 | Output | User story **+ human approve/reject/feedback step** |
| 16 | Where it runs | Local first, then deploy to GCP |
| 17 | Users | Shared with the team |
| 18 | Code home | This folder, as a Git repo |
| 19 | Agent language | Python |
| 20 | Working style | Claude builds and explains each step |
| 21 | Deadline | No fixed date |
| 22 | Per-service notes | Yes |
| – | Python version | Try the installed 3.14 first; add 3.12/3.13 only if something fails |
| – | Java | Install **JDK 21** so PetClinic can be built and tested |
| – | Team sharing | **Private GitHub repo**, pushed only when Dipesh says so |

## Local machine (checked)
| Tool | Status |
|---|---|
| gcloud | 583.0.0, signed in as itmcsystemsdigital@gmail.com (current default project: `zevyio`, which will **not** be used) |
| Python | 3.14.0 only; pip works via `python -m pip` |
| Git | 2.54 |
| GitHub CLI | 2.96, signed in as `dipesharma29` |
| Node | 24.18 |
| Java | Not installed (JDK 21 to be installed) |
| uv | Not installed |

## Points to keep in mind (stated openly, not assumed)
- **Real transcript:** it includes colleagues' names and discussion. It will be sent to Gemini in the ITMC project and may end up in Jira tickets. That's internal to ITMC, but the team should know.
- **Jira connector vs the agent's own access:** the connector lets *Claude* create sample tickets. The *prototype agent* still needs its own Jira credentials (an API token you create and store in Secret Manager or a local `.env`) to read and write Jira at runtime.
- **Cost watch-points:** a deployed Vector Search endpoint, Vertex AI Search data stores and Agent Engine deployments can bill while idle. Each will be set up last, used briefly, and torn down after the comparison unless you decide otherwise.

## Confirmed (20 Nov 2026)
- **GitHub:** use `dipesharma29` only.
- **GCP project:** created by Dipesh. Name "AI SDLC", ID **`ai-sdlc-515307`**, number 207741542267. **No billing linked** (Dipesh will link it when needed). Some APIs are already on by default (BigQuery family, Cloud Storage, Datastore, Logging, Monitoring, Trace). Vertex AI, Cloud Run, Firestore and the others are **not** on yet.
- **Jira connector works:** site `itmcsystems-team-r6zdxryt.atlassian.net`, read-write. Existing projects: `KAN` "Big 3" (3 issues) and `SAM1` "(Example) Billing System Dev" (10 issues). Neither is for the prototype yet.
- **Cost rule:** always ask before turning on anything that can bill.
- **Transcript sharing:** fine. The team is working together on this.
- **Agent's own Jira token:** Dipesh will create it later.

## Still open
- Which Jira project the prototype should use (see chat).
- Without billing, Vertex AI / Gemini calls, Cloud Run and Firestore can't be used in this project. Agree how to handle that before any GCP step.
