# GCP Services for the AI DLC Prototype: Team Notes

Draft, 20 Nov 2026. These notes are written from general knowledge, before hands-on use. Anything marked **(verify)** must be checked against Google's docs or pricing pages, and each section gets updated after we actually use the service.
Project: `ai-sdlc-515307` (billing not linked yet).

**Cost rule for this prototype:** nothing that can bill gets turned on without Dipesh's OK.

---

## 1. Gemini on Vertex AI (Model Garden)
- **What:** Google's foundation models, called through Vertex AI. **Model Garden** is the catalogue in the console that lists Google, partner and open models and shows how to enable or deploy each one.
- **Our use:** the brain of every agent. ADK calls Gemini when `GOOGLE_GENAI_USE_VERTEXAI=TRUE` is set.
- **Billing model:** pay per token (input and output). Nothing bills while it's idle.
- **Needs:** the Vertex AI API (`aiplatform.googleapis.com`) and a linked billing account.
- **Watch:** "Flash" models are much cheaper than "Pro". Default to Flash for the prototype. Check the current model versions in Model Garden **(verify)**.

## 2. ADK (Agent Development Kit)
- **What:** Google's open-source framework (Python, plus other languages) for building agents: an LLM, an instruction, and tools. Multi-agent setups are supported with sub-agents and workflow agents (sequential, parallel, loop).
- **Our use:** the Requirements Agent (`prototype/requirements_agent`). Later, the other SDLC agents and the orchestrator.
- **Billing:** free (it's a library). You only pay for the model calls and the hosting.
- **Useful bits:**
  - `adk web` is a local browser UI for chatting with agents and inspecting each step.
  - `adk run` runs the agent in the terminal.
  - Tools are plain Python functions.
  - `require_confirmation` on a tool pauses for human approval. This is our human gate **(verify the behaviour in the installed version)**.

## 3. Agent Engine (Vertex AI Agent Engine)
- **What:** managed hosting for agents built with ADK and other frameworks. It provides sessions, memory, scaling and tracing.
- **Our use:** the "deploy to GCP" step after the agent works locally.
- **Billing:** charged for the compute and memory a deployed agent uses **(verify whether it bills while idle)**. Delete test deployments after use.
- **Alternative:** Cloud Run (section 7). Agent Engine gives managed sessions and memory; Cloud Run gives more control.

## 4. Agent Garden
- **What:** a catalogue in the console of sample agents and tools (ready-made ADK samples) that you can copy and adapt.
- **Our use:** look for samples close to ours (code understanding, RAG, human-in-the-loop) before building more ourselves.
- **Billing:** browsing is free. Deploying a sample bills like any other agent.

## 5. RAG options (we're comparing all three on the same PetClinic data)
| Option | What it is | Effort | Billing shape |
|---|---|---|---|
| **Vertex AI RAG Engine** | Managed RAG pipeline: import files (GCS, Drive, etc.), it chunks, embeds and retrieves. Plugs straight into ADK as a retrieval tool. | Low | Embeddings plus its storage backend **(verify the tier and whether the default backend has a standing cost)** |
| **Vertex AI Search** (Agent Builder) | Managed enterprise search over websites, documents and structured data, with ranking built in. | Lowest | Per query plus indexed data storage **(verify)** |
| **Vector Search** | Raw, high-scale vector database. You create embeddings, build an index and deploy it to an endpoint. | Highest | **A deployed index endpoint bills per hour while deployed, even with zero queries.** Deploy only for the test, then undeploy. |

- **Plan:** use the same inputs (PetClinic code, sample tickets, transcript) and the same 5–10 questions for each option. Compare answer quality, setup effort and cost.
- Prachi's point: we're not building a data project, so we only keep what's needed.

## 6. Embeddings
- **What:** models that turn text or code into vectors. Vertex AI has text embedding models **(verify the current model name)**.
- **Billing:** per token embedded. A one-off index of PetClinic (around 100 files) should be very small.

## 7. Cloud Run
- **What:** serverless containers. It scales to zero, so it costs nothing while idle when min instances = 0.
- **Our use:** host the ADK agent (or later the orchestrator/UI) as an alternative to Agent Engine.
- **Watch:** keep `min-instances=0`. Turn on "CPU always allocated" only if needed.

## 8. Firestore
- **What:** serverless NoSQL document database.
- **Our use:** run state for the orchestrator (which step each run is on, approvals, feedback).
- **Billing:** per read, write and storage, with a daily free quota **(verify)**. No idle cost beyond stored data.

## 9. Cloud Storage
- **What:** object storage (buckets).
- **Our use:** raw inputs (transcripts, docs, a code snapshot) for the RAG imports.
- **Billing:** per GB stored and per operation. The prototype's data is tiny.

## 10. Secret Manager
- **What:** stores API keys and tokens, such as the agent's Jira token, once we deploy.
- **Billing:** per secret version per month plus access operations; small **(verify)**.

## Not planned for now
- **BigQuery:** Prachi said it's probably not needed. Its APIs are already on by default in the project, but that costs nothing unless used.

---

## APIs we'll need to turn on (each one only with Dipesh's OK)
| API | For | Can it bill? |
|---|---|---|
| `aiplatform.googleapis.com` | Gemini, Agent Engine, RAG Engine, Vector Search | Yes, when used |
| `discoveryengine.googleapis.com` | Vertex AI Search | Yes, when used |
| `run.googleapis.com` | Cloud Run | Yes, when used |
| `firestore.googleapis.com` | Firestore | Yes, when used (free quota) |
| `secretmanager.googleapis.com` | Secret Manager | Yes, small |
| `cloudbuild.googleapis.com` / `artifactregistry.googleapis.com` | Building and storing containers for Cloud Run / Agent Engine | Yes, small |
