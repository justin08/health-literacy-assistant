# Health Literacy Assistant - Technical Documentation

**project:** retrieval-augmented patient health literacy assistant for ehr data
**date:** april 19, 2026
**team size:** 5
**backend lead:** justin adelman

---

## 1. project overview

a rag-based tool that translates medical jargon from patient health records (labs, medications, conditions) into plain-language summaries grounded in authoritative medical references. patients log in, view their ehr data, and get readable explanations powered by vector retrieval + llm generation.

---

## 2. architecture

```
┌─────────────────────┐     ┌──────────────────────────────────────┐     ┌─────────────────────┐
│   layer 1: data     │     │   layer 2: llamaindex ("librarian")  │     │ layer 3: langchain  │
│                     │     │                                      │     │   ("advocate")      │
│ synthea patients    │────>│ fhir parser → chunker → embedder     │     │                     │
│ (fhir json)         │     │          ↓                           │     │ langchain agent     │
│                     │     │ chromadb (vector store)               │────>│ + prompt templates  │────> llm provider
│ medlineplus kb      │────>│          ↓                           │     │          ↓          │     (openai gpt-5.4-nano)
│ (xml + drug json)   │     │ context query engine                 │     │ jargon-free summary │
└─────────────────────┘     └──────────────────────────────────────┘     └─────────┬───────────┘
                                                                                  │
                                                                                  ↓
                                                                        ┌─────────────────────┐
                                                                        │ patient dashboard   │
                                                                        │ (streamlit ui)      │
                                                                        └─────────────────────┘
```

---

## 3. tech stack

| layer        | technology                              | version    |
|-------------|------------------------------------------|------------|
| language     | python                                  | 3.12       |
| backend      | fastapi + uvicorn                       | 0.135.3    |
| frontend     | streamlit                               | 1.56.0     |
| vector db    | chromadb                                | 1.5.5      |
| embeddings   | sentence-transformers (all-MiniLM-L6-v2)| 2.7.0+     |
| llm          | openai (gpt-5.4-nano)                   | 2.30.0     |
| auth         | pyjwt + bcrypt                          | 2.10.1     |
| readability  | textstat (flesch-kincaid)               | 0.7.13     |
| containers   | docker + docker-compose                 | -          |
| deployment   | aws ecs fargate                         | -          |
| ci/cd        | github actions                          | -          |
| data         | pydantic + pydantic-settings            | 2.12.5     |

---

## 4. project structure

```
health-literacy-assistant/
├── .github/workflows/
│   └── deploy.yml                     # ci/cd: build → ecr → ecs
├── .aws/
│   └── task-definition.json           # ecs fargate task config
├── backend/
│   ├── app/
│   │   ├── main.py                    # fastapi app + lifespan + cors
│   │   ├── config.py                  # env settings (pydantic)
│   │   ├── auth.py                    # jwt create/validate
│   │   ├── models/
│   │   │   └── schemas.py             # request/response models
│   │   ├── routes/
│   │   │   ├── auth_routes.py         # POST /api/auth/login
│   │   │   ├── patient_routes.py      # GET /api/patients/*
│   │   │   └── explain_routes.py      # POST /api/explain
│   │   └── services/
│   │       ├── rag_service.py         # main rag orchestrator
│   │       ├── llm_client.py          # openai/anthropic abstraction
│   │       ├── kb_retriever.py        # vector search interface
│   │       ├── kb_vectorstore.py      # chromadb wrapper
│   │       ├── kb_embedder.py         # sentence-transformers
│   │       ├── kb_chunker.py          # doc splitting (1500 char / 200 overlap)
│   │       ├── kb_sources.py          # medlineplus xml + drug json parser
│   │       ├── patient_service.py     # mock patient data + auth
│   │       ├── prompts.py             # system + specialized prompt templates
│   │       ├── safety.py              # medical advice detection
│   │       └── evaluation.py          # readability + jargon scoring
│   ├── data/
│   │   ├── chroma_store/              # persisted vector index
│   │   ├── knowledge_docs/
│   │   │   ├── processed/             # 1,132 cleaned .txt docs
│   │   │   └── raw/                   # medlineplus xml + drug jsons
│   │   └── cleaned_patient_data.json  # synthea fhir-like records
│   ├── scripts/
│   │   ├── build_index.py             # build chromadb from docs
│   │   └── fetch_drugs.py             # pull drug data from medlineplus api
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                         # main streamlit app (multi-page)
│   ├── pages/
│   │   ├── login.py                   # auth ui
│   │   └── admin.py                   # admin patient list
│   ├── utils/
│   │   ├── api_client.py              # backend client w/ mock fallback
│   │   └── mock_data.py               # offline demo data
│   ├── .streamlit/
│   │   ├── config.toml                # theme + server settings
│   │   └── custom.css                 # accessibility styles
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 5. api endpoints

| method | path                                  | auth     | description                        |
|--------|---------------------------------------|----------|------------------------------------|
| GET    | `/api/health`                         | none     | health check (backend, db, rag)    |
| POST   | `/api/auth/login`                     | none     | authenticate, returns jwt          |
| GET    | `/api/patients`                       | admin    | list all patients                  |
| GET    | `/api/patients/{id}/conditions`       | jwt      | patient conditions/diagnoses       |
| GET    | `/api/patients/{id}/medications`      | jwt      | patient medications                |
| GET    | `/api/patients/{id}/observations`     | jwt      | patient lab results                |
| POST   | `/api/explain`                        | jwt      | translate medical term → plain text|

---

## 6. rag pipeline flow

```
user query ("what is hemoglobin a1c?")
        │
        ▼
  ┌─────────────┐
  │  embedder   │  sentence-transformers/all-MiniLM-L6-v2 (384-dim)
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  chromadb   │  cosine similarity, top-k=5 retrieval
  │  (5000+     │
  │   chunks)   │
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  prompt     │  system prompt + retrieved context + user query
  │  builder    │  (6th-8th grade reading level target)
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  llm call   │  gpt-5.4-nano (temp=0.2, max_tokens=1024)
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  safety     │  check for medical advice patterns
  │  check      │  append doctor consultation reminder if missing
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  evaluation │  flesch-kincaid grade (target ≤ 8.0)
  │             │  flesch reading ease (target ≥ 60.0)
  │             │  jargon detection (70+ terms)
  └──────┬──────┘
         ▼
  response: { plain_language, sources[], readability_score }
```

---

## 7. knowledge base

| source                  | format     | count     | content                          |
|------------------------|------------|-----------|----------------------------------|
| medlineplus topics     | xml → txt  | ~1,032    | conditions, diseases, tests      |
| medlineplus drugs      | json → txt | ~100      | medications, dosages, side effects|
| **total indexed**      |            | **1,132** | chunked into **~5,000+ vectors** |

chunking: 1,500 chars max, 200 char overlap, sentence-boundary splitting

---

## 8. security model

| feature                  | implementation                                     |
|--------------------------|---------------------------------------------------|
| auth method              | jwt bearer tokens (hs256)                         |
| token expiry             | 8 hours                                           |
| password storage         | plaintext (mock data only, bcrypt available)       |
| access control           | role-based (admin vs patient)                     |
| patient data isolation   | patients can only access own records              |
| cors                     | configurable origins list                         |
| secrets in prod          | aws systems manager parameter store               |
| safety checks            | regex-based medical advice detection on llm output|

---

## 9. deployment

### infrastructure (aws)

| resource            | name/value                                              |
|--------------------|---------------------------------------------------------|
| ecr repos          | `hla-backend`, `hla-frontend`                           |
| ecs cluster        | `hla-cluster`                                           |
| ecs service        | `hla-service`                                           |
| task def           | `hla-task` (fargate, 0.5 vcpu, 1gb ram)                |
| log group          | `/ecs/hla` (cloudwatch)                                 |
| ssm secrets        | `/hla/jwt-secret`, `/hla/openai-api-key`               |
| region             | us-east-1                                               |

### ci/cd flow

```
push to main → github actions → build docker images → push to ecr → update ecs task def → deploy to fargate
```

images tagged with both commit sha and `latest`.

---

## 10. plan vs actual progress

### original plan tasks (from sprint #2 doc)

| id  | task                          | planned  | status         | notes                                           |
|-----|-------------------------------|----------|----------------|------------------------------------------------|
| T1  | data environment setup        | week 1   | done           | synthea data generated, fhir-like json parsed  |
| T2  | knowledge base curation       | week 2   | done           | 1,132 docs from medlineplus (topics + drugs)   |
| T3  | vector database indexing      | week 2   | done           | chromadb indexed, ~5,000+ chunks               |
| T4  | rag pipeline development      | week 3   | done           | full pipeline: embed → retrieve → generate     |
| T5  | llm integration               | week 3   | done           | openai primary, anthropic fallback available   |
| T6  | ui/frontend development       | week 4   | done           | streamlit multi-page app with accessibility css|
| T7  | backend-frontend integration  | week 4   | done           | api client with mock fallback                  |
| T8  | testing & validation          | week 5   | **not started** | no test files exist in the repo                |
| T9  | refinement & prompt tuning    | week 5   | **partial**    | prompts written, no iteration logs             |
| T10 | final documentation & demo    | week 6   | **not started** | no readme, no demo video, no final report      |

---

## 11. what's done (completed work)

- full fastapi backend with 3 route modules and jwt auth
- complete rag pipeline: chunking → embedding → vector retrieval → llm generation
- 1,132 knowledge base documents indexed in chromadb
- safety checks (medical advice detection, doctor reminder enforcement)
- readability scoring (flesch-kincaid grade level + reading ease)
- jargon detection with 70+ medical terms library
- multi-provider llm support (openai + anthropic fallback)
- streamlit frontend with login, dashboard, records, translation assistant, admin panel
- api client with graceful fallback to mock data
- docker + docker-compose for local dev
- aws ecs fargate deployment with github actions ci/cd
- accessibility-first css (large fonts, high contrast, simple navigation)

---

## 12. what's missing — next to-do list

### priority 1: testing & validation (T8) — critical

the repo has zero tests. this is the biggest gap.

- [ ] **unit tests for rag pipeline**
  - test `kb_chunker.py`: verify chunk sizes, overlap, metadata preservation
  - test `kb_embedder.py`: verify embedding dimensions (384), batch processing
  - test `kb_vectorstore.py`: verify add/query/clear operations
  - test `kb_retriever.py`: verify retrieval returns ranked results with scores

- [ ] **unit tests for services**
  - test `safety.py`: verify medical advice patterns are caught
  - test `evaluation.py`: verify readability scoring against known text samples
  - test `patient_service.py`: verify user lookup, credential validation, access control
  - test `prompts.py`: verify template formatting with various inputs

- [ ] **api integration tests**
  - test `/api/auth/login` with valid/invalid credentials
  - test `/api/patients` admin access control
  - test `/api/patients/{id}/conditions|medications|observations` with role checks
  - test `/api/explain` end-to-end with a known term

- [ ] **rag quality evaluation**
  - create a test set of 20-30 medical terms with expected plain-language outputs
  - measure readability scores across the test set (target: flesch-kincaid ≤ 8.0)
  - measure jargon leakage rate (unexplained medical terms in output)
  - measure faithfulness (are claims grounded in retrieved context?)
  - document success and failure cases with examples

- [ ] **frontend smoke tests**
  - verify login flow works
  - verify patient data renders correctly
  - verify explain feature returns and displays results

### priority 2: refinement & prompt tuning (T9) — high

- [ ] **prompt iteration**
  - run evaluation test set, identify weak spots
  - adjust system prompt for terms that still produce jargon
  - tune retrieval parameters (top_k, chunk size) based on result quality
  - test different temperature values for explanation variety vs consistency

- [ ] **retrieval quality**
  - add keyword fallback when semantic search returns low-confidence results
  - consider re-ranking retrieved chunks before passing to llm
  - evaluate if chunk size (1500 chars) is optimal or needs adjustment

- [ ] **llm output improvements**
  - add response caching to avoid redundant api calls for repeated terms
  - improve fallback behavior when llm is unavailable (better static explanations)
  - test with different models to compare explanation quality

### priority 3: documentation & demo (T10) — required for submission

- [ ] **readme.md**
  - project description and motivation
  - setup instructions (local dev + docker)
  - environment variables reference
  - api documentation
  - architecture overview
  - team member contributions

- [ ] **final project report**
  - background and justification (from sprint #2 doc)
  - technical design decisions and tradeoffs
  - evaluation results with metrics
  - known limitations and future work
  - lessons learned

- [ ] **demo video (5 minutes)**
  - walkthrough of patient login flow
  - show lab results → plain language translation
  - show medication explanation
  - show condition explanation
  - highlight readability scores and source attribution

- [ ] **code documentation**
  - ensure all modules have clear docstrings
  - add inline comments for non-obvious logic
  - clean up any dead code or unused imports

### priority 4: polish & hardening — nice to have

- [ ] **documentreference support**
  - the original plan included parsing unstructured clinical notes
  - currently not implemented — only observation, condition, medicationrequest are supported
  - add clinical note summarization if time permits

- [ ] **real database for patient data**
  - currently using json file with mock data
  - could add sqlite or postgres for persistence
  - would enable proper password hashing with bcrypt (already in dependencies)

- [ ] **conversation history**
  - each query is independent right now
  - could add session-based context so follow-up questions work naturally

- [ ] **before/after translation view**
  - the original mockup showed a side-by-side "before (jargon)" and "after (plain)" view
  - current ui shows the plain explanation but not the original clinical text side-by-side
  - match the mockup from the sprint doc

- [ ] **expanded knowledge base**
  - add more drug entries beyond the current ~100
  - consider mayo clinic or other authoritative sources
  - add coverage for common lab test reference ranges

---

## 13. risk status update

| risk                   | original concern                        | current status                                    |
|------------------------|-----------------------------------------|--------------------------------------------------|
| technical complexity   | multiple complex technologies           | **mitigated** — all components integrated         |
| llm hallucination      | incorrect medical info                  | **partially mitigated** — safety checks + rag grounding in place, but not validated with test set |
| data quality           | kb source limitations                   | **mitigated** — medlineplus is authoritative, 1,132 docs indexed |
| scope creep            | feature bloat                           | **managed** — stuck to mvp, documentreference deferred |
| llm api dependencies   | cost, rate limits, outages              | **mitigated** — dual provider support + mock fallback |
| evaluation subjectivity| measuring "good enough"                 | **open risk** — readability scoring built but no systematic evaluation run yet |

---

## 14. team action items

| who      | task                                    | priority | target     |
|----------|-----------------------------------------|----------|------------|
| justin   | write backend unit tests (rag + services)| p1       | this week  |
| team     | create evaluation test set (20-30 terms) | p1       | this week  |
| team     | run rag quality evaluation + document    | p1       | next week  |
| team     | prompt tuning based on eval results      | p2       | next week  |
| team     | write readme.md                          | p3       | next week  |
| team     | write final project report               | p3       | week after |
| team     | record 5-min demo video                  | p3       | week after |
| justin   | add response caching                     | p4       | if time    |
| team     | documentreference support                | p4       | if time    |

---

## 15. how to run locally

```bash
# clone and configure
git clone <repo-url>
cp .env.example .env
# add your OPENAI_API_KEY to .env

# docker (recommended)
docker-compose up --build

# or run separately:
# backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend && pip install -r requirements.txt
streamlit run app.py

# build vector index (if needed)
cd backend && python scripts/build_index.py
```

**demo credentials:** any patient name as username (lowercase, underscored) with password `password123`, or `admin` / `admin123`
