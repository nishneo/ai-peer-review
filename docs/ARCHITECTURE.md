# AI Peer Review - Architecture & Design

This document provides comprehensive technical documentation including architecture diagrams, implementation details, and development notes.

---

## Project Overview

AI Peer Review is a 3-stage deliberation system where multiple LLMs collaboratively answer user questions. The key innovation is anonymized peer review in Stage 2, preventing models from playing favorites.

---

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "Frontend (React)"
        FE[React App<br/>localhost:5173]
    end

    subgraph "Backend (FastAPI)"
        API[FastAPI Server<br/>main.py]
        COUNCIL[Council Orchestrator<br/>council.py]
        OPENROUTER[OpenRouter Client<br/>openrouter.py]
        STORAGE[Storage Layer<br/>storage.py]
        CONFIG[Configuration<br/>config.py]
    end

    subgraph "External Services"
        OR[OpenRouter API<br/>openrouter.ai]
        subgraph "LLM Models"
            M1[Model 1]
            M2[Model 2]
            M3[Model 3]
            M4[Model 4]
        end
    end

    subgraph "File System"
        FS[(JSON Files<br/>data/conversations/)]
    end

    FE <-->|HTTP/SSE| API
    API --> COUNCIL
    COUNCIL --> OPENROUTER
    OPENROUTER -->|HTTP| OR
    OR --> M1 & M2 & M3 & M4
    API --> STORAGE
    STORAGE <-->|Read/Write| FS
    COUNCIL --> CONFIG
    OPENROUTER --> CONFIG
```

---

## 2. Module Dependency Diagram

```mermaid
graph LR
    subgraph "Backend Modules"
        main[main.py<br/>FastAPI App]
        council[council.py<br/>Orchestration Logic]
        openrouter[openrouter.py<br/>API Client]
        storage[storage.py<br/>Persistence]
        config[config.py<br/>Configuration]
    end

    main --> council
    main --> storage
    council --> openrouter
    council --> config
    openrouter --> config
    storage --> config

    style main fill:#e1f5fe
    style council fill:#fff3e0
    style openrouter fill:#f3e5f5
    style storage fill:#e8f5e9
    style config fill:#fce4ec
```

---

## 3. The 3-Stage Process

```mermaid
flowchart TB
    subgraph INPUT
        UQ[User Query]
    end

    subgraph "STAGE 1: Collect Individual Responses"
        S1[Send query to all<br/>Panel Models]
        M1A[Model 1<br/>Response]
        M2A[Model 2<br/>Response]
        M3A[Model 3<br/>Response]
        M4A[Model 4<br/>Response]
        S1R[Stage 1 Results<br/>4 Individual Responses]
    end

    subgraph "STAGE 2: Peer Rankings"
        S2[Send anonymized responses<br/>to all models for ranking]
        ANON[Anonymize Responses<br/>Response A, B, C, D]
        M1R[Model 1<br/>Rankings]
        M2R[Model 2<br/>Rankings]
        M3R[Model 3<br/>Rankings]
        M4R[Model 4<br/>Rankings]
        AGG[Calculate Aggregate<br/>Rankings]
        S2R[Stage 2 Results<br/>Rankings + Analysis]
    end

    subgraph "STAGE 3: Synthesizer"
        S3[Synthesizer Model receives<br/>all context]
        SYNTH[Synthesize Final<br/>Response]
        S3R[Stage 3 Result<br/>Final Answer]
    end

    subgraph OUTPUT
        RESP[Complete Response<br/>to User]
    end

    UQ --> S1
    S1 --> M1A & M2A & M3A & M4A
    M1A & M2A & M3A & M4A --> S1R
    S1R --> ANON
    ANON --> S2
    S2 --> M1R & M2R & M3R & M4R
    M1R & M2R & M3R & M4R --> AGG
    AGG --> S2R
    S1R --> S3
    S2R --> S3
    S3 --> SYNTH
    SYNTH --> S3R
    S3R --> RESP

    style INPUT fill:#e3f2fd
    style OUTPUT fill:#e8f5e9
```

---

## 4. Backend Module Details

### `config.py`
- Contains `COUNCIL_MODELS` (list of OpenRouter model identifiers)
- Contains `CHAIRMAN_MODEL` (model that synthesizes final answer)
- Uses environment variable `OPENROUTER_API_KEY` from `.env`
- Backend runs on **port 8001**

### `openrouter.py`
- `query_model()`: Single async model query
- `query_models_parallel()`: Parallel queries using `asyncio.gather()`
- Returns dict with 'content' and optional 'reasoning_details'
- Graceful degradation: returns None on failure, continues with successful responses

### `council.py` - The Core Logic
- `stage1_collect_responses()`: Parallel queries to all panel models
- `stage2_collect_rankings()`:
  - Anonymizes responses as "Response A, B, C, etc."
  - Creates `label_to_model` mapping for de-anonymization
  - Prompts models to evaluate and rank (with strict format requirements)
  - Returns tuple: (rankings_list, label_to_model_dict)
  - Each ranking includes both raw text and `parsed_ranking` list
- `stage3_synthesize_final()`: Synthesizer compiles from all responses + rankings
- `parse_ranking_from_text()`: Extracts "FINAL RANKING:" section
- `calculate_aggregate_rankings()`: Computes average rank position across all peer evaluations

### `storage.py`
- JSON-based conversation storage in `data/conversations/`
- Each conversation: `{id, created_at, messages[]}`
- Assistant messages contain: `{role, stage1, stage2, stage3}`
- Note: metadata (label_to_model, aggregate_rankings) is NOT persisted to storage

### `main.py`
- FastAPI app with CORS enabled
- POST `/api/conversations/{id}/message` returns metadata in addition to stages
- Metadata includes: label_to_model mapping and aggregate_rankings

---

## 5. API Request Sequence

```mermaid
sequenceDiagram
    participant Client as Frontend
    participant API as FastAPI (main.py)
    participant Storage as storage.py
    participant Council as council.py
    participant OR as openrouter.py
    participant Models as OpenRouter API

    Note over Client,Models: User sends a message in a conversation

    Client->>API: POST /api/conversations/{id}/message/stream
    API->>Storage: get_conversation(id)
    Storage-->>API: conversation data

    API->>Storage: add_user_message(id, content)

    Note over API,Models: Stage 1: Collect Individual Responses
    API-->>Client: SSE: stage1_start
    API->>Council: stage1_collect_responses(query)
    Council->>OR: query_models_parallel(COUNCIL_MODELS, messages)
    
    par Parallel Model Queries
        OR->>Models: POST (Model 1)
        OR->>Models: POST (Model 2)
        OR->>Models: POST (Model 3)
        OR->>Models: POST (Model 4)
        Models-->>OR: Response 1
        Models-->>OR: Response 2
        Models-->>OR: Response 3
        Models-->>OR: Response 4
    end
    
    OR-->>Council: {model: response, ...}
    Council-->>API: stage1_results
    API-->>Client: SSE: stage1_complete

    Note over API,Models: Stage 2: Collect Rankings
    API-->>Client: SSE: stage2_start
    API->>Council: stage2_collect_rankings(query, stage1_results)
    Council->>Council: Anonymize responses (A, B, C, D)
    Council->>OR: query_models_parallel(COUNCIL_MODELS, ranking_prompt)
    
    par Parallel Ranking Queries
        OR->>Models: POST (Model 1 rankings)
        OR->>Models: POST (Model 2 rankings)
        OR->>Models: POST (Model 3 rankings)
        OR->>Models: POST (Model 4 rankings)
        Models-->>OR: Rankings
    end
    
    OR-->>Council: {model: ranking, ...}
    Council->>Council: parse_ranking_from_text()
    Council->>Council: calculate_aggregate_rankings()
    Council-->>API: stage2_results, label_to_model
    API-->>Client: SSE: stage2_complete

    Note over API,Models: Stage 3: Synthesizer
    API-->>Client: SSE: stage3_start
    API->>Council: stage3_synthesize_final(query, s1, s2)
    Council->>OR: query_model(CHAIRMAN_MODEL, synthesizer_prompt)
    OR->>Models: POST (Synthesizer)
    Models-->>OR: Final synthesis
    OR-->>Council: response
    Council-->>API: stage3_result
    API-->>Client: SSE: stage3_complete

    API->>Storage: add_assistant_message(id, s1, s2, s3)
    API-->>Client: SSE: complete
```

---

## 6. Data Models

```mermaid
erDiagram
    CONVERSATION {
        string id PK "UUID"
        string created_at "ISO timestamp"
        string title "Auto-generated"
        array messages "List of messages"
    }

    USER_MESSAGE {
        string role "user"
        string content "User's query"
    }

    ASSISTANT_MESSAGE {
        string role "assistant"
        array stage1 "Individual responses"
        array stage2 "Rankings"
        object stage3 "Final synthesis"
    }

    STAGE1_RESULT {
        string model "Model identifier"
        string response "Model's response"
    }

    STAGE2_RESULT {
        string model "Model identifier"
        string ranking "Full ranking text"
        array parsed_ranking "Parsed labels"
    }

    STAGE3_RESULT {
        string model "Synthesizer model"
        string response "Synthesized answer"
    }

    CONVERSATION ||--o{ USER_MESSAGE : contains
    CONVERSATION ||--o{ ASSISTANT_MESSAGE : contains
    ASSISTANT_MESSAGE ||--|{ STAGE1_RESULT : "has stage1"
    ASSISTANT_MESSAGE ||--|{ STAGE2_RESULT : "has stage2"
    ASSISTANT_MESSAGE ||--|| STAGE3_RESULT : "has stage3"
```

---

## 7. REST API Endpoints

```mermaid
graph TB
    subgraph "API Endpoints"
        GET_ROOT["GET /<br/>Health Check"]
        GET_LIST["GET /api/conversations<br/>List all conversations"]
        POST_CREATE["POST /api/conversations<br/>Create new conversation"]
        GET_CONV["GET /api/conversations/{id}<br/>Get conversation details"]
        POST_MSG["POST /api/conversations/{id}/message<br/>Send message (blocking)"]
        POST_STREAM["POST /api/conversations/{id}/message/stream<br/>Send message (SSE streaming)"]
    end

    subgraph "Response Types"
        JSON[JSON Response]
        SSE[Server-Sent Events<br/>Real-time streaming]
    end

    GET_ROOT --> JSON
    GET_LIST --> JSON
    POST_CREATE --> JSON
    GET_CONV --> JSON
    POST_MSG --> JSON
    POST_STREAM --> SSE

    style POST_STREAM fill:#e8f5e9
    style SSE fill:#e8f5e9
```

---

## 8. SSE Event Flow

```mermaid
stateDiagram-v2
    [*] --> stage1_start: Request received
    stage1_start --> stage1_complete: Models respond
    stage1_complete --> stage2_start: Begin rankings
    stage2_start --> stage2_complete: Rankings collected
    stage2_complete --> stage3_start: Begin synthesis
    stage3_start --> stage3_complete: Synthesizer responds
    stage3_complete --> title_complete: (if first message)
    stage3_complete --> complete: (if not first)
    title_complete --> complete: Title generated
    complete --> [*]: Stream ends

    note right of stage1_start: {"type": "stage1_start"}
    note right of stage1_complete: {"type": "stage1_complete", "data": [...]}
    note right of stage2_complete: {"type": "stage2_complete", "data": [...], "metadata": {...}}
    note right of stage3_complete: {"type": "stage3_complete", "data": {...}}
```

---

## 9. Frontend Structure

### `App.jsx`
- Main orchestration: manages conversations list and current conversation
- Handles message sending and metadata storage
- Important: metadata is stored in the UI state for display but not persisted to backend JSON

### `components/ChatInterface.jsx`
- Multiline textarea (3 rows, resizable)
- Enter to send, Shift+Enter for new line
- User messages wrapped in markdown-content class for padding

### `components/Stage1.jsx`
- Tab view of individual model responses
- ReactMarkdown rendering with markdown-content wrapper

### `components/Stage2.jsx`
- **Critical Feature**: Tab view showing RAW evaluation text from each model
- De-anonymization happens CLIENT-SIDE for display (models receive anonymous labels)
- Shows "Extracted Ranking" below each evaluation so users can validate parsing
- Aggregate rankings shown with average position and vote count

### `components/Stage3.jsx`
- Final synthesized answer from synthesizer model
- Green-tinted background to highlight conclusion

### Styling
- Light mode theme with warm amber accent color (#d97706)
- Uses CSS variables for theming
- DM Sans font for UI, JetBrains Mono for code
- Global markdown styling in `index.css`

---

## 10. Key Design Decisions

### Stage 2 Prompt Format
The Stage 2 prompt is very specific to ensure parseable output:
```
1. Evaluate each response individually first
2. Provide "FINAL RANKING:" header
3. Numbered list format: "1. Response C", "2. Response A", etc.
4. No additional text after ranking section
```

### De-anonymization Strategy
- Models receive: "Response A", "Response B", etc.
- Backend creates mapping: `{"Response A": "openai/gpt-4o", ...}`
- Frontend displays model names in **bold** for readability
- Users see explanation that original evaluation used anonymous labels
- This prevents bias while maintaining transparency

### Error Handling Philosophy
- Continue with successful responses if some models fail (graceful degradation)
- Never fail the entire request due to single model failure
- Log errors but don't expose to user unless all models fail

### UI/UX Transparency
- All raw outputs are inspectable via tabs
- Parsed rankings shown below raw text for validation
- Users can verify system's interpretation of model outputs

---

## 11. Design Patterns

| Pattern | Usage | Location |
|---------|-------|----------|
| **Async/Await** | Non-blocking I/O for API calls | `openrouter.py`, `council.py` |
| **Parallel Processing** | `asyncio.gather` for concurrent model queries | `openrouter.query_models_parallel()` |
| **Server-Sent Events** | Real-time streaming updates | `main.py` streaming endpoint |
| **Repository Pattern** | JSON file-based storage abstraction | `storage.py` |
| **Configuration Injection** | Centralized config via module | `config.py` |
| **Event-Driven Updates** | SSE events for each stage completion | `main.py` event generator |

---

## 12. Common Gotchas

1. **Module Import Errors**: Always run backend as `python -m backend.main` from project root
2. **CORS Issues**: Frontend must match allowed origins in `main.py` CORS middleware
3. **Ranking Parse Failures**: If models don't follow format, fallback regex extracts any "Response X" patterns
4. **Missing Metadata**: Metadata is ephemeral (not persisted), only available in API responses

---

## 13. Port Configuration

- Backend: 8001
- Frontend: 5173 (Vite default)
- Update both `backend/main.py` and `frontend/src/api.js` if changing

---

## 14. File Summary

| File | Purpose | Lines |
|------|---------|-------|
| `main.py` | FastAPI application, REST endpoints, CORS | ~200 |
| `council.py` | 3-stage orchestration logic | ~336 |
| `openrouter.py` | HTTP client for OpenRouter API | ~80 |
| `storage.py` | JSON file persistence | ~173 |
| `config.py` | Environment and model configuration | ~27 |

---

## Data Flow Summary

```
User Query
    ↓
Stage 1: Parallel queries → [individual responses]
    ↓
Stage 2: Anonymize → Parallel ranking queries → [evaluations + parsed rankings]
    ↓
Aggregate Rankings Calculation → [sorted by avg position]
    ↓
Stage 3: Synthesizer compilation with full context
    ↓
Return: {stage1, stage2, stage3, metadata}
    ↓
Frontend: Display with tabs + validation UI
```

The entire flow is async/parallel where possible to minimize latency.

