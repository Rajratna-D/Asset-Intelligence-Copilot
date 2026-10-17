# 📐 FlytBase Asset Intelligence Copilot: UML & System Diagrams

This document contains the complete Unified Modeling Language (UML) specifications for the **FlytBase Asset Intelligence Copilot**. All diagrams are formatted in native GitHub-compatible **Mermaid** syntax.

---

## 1. System Component Diagram (UML Component)

Describes the modular decomposition of the frontend, backend services, security boundaries, and data tier.

```mermaid
graph TB
    subgraph Client_Layer ["Client Presentation Layer (Port 3000)"]
        UI["React 18 + Vite SPA"]
        Slider["Contextual Mode Slider<br/>(Text / Table / Line / Heatmap / Map)"]
        GenDash["Generative UI Dashboard"]
        SecModal["Security Guardrails Modal"]
        CitationDrawer["Interactive Citation Drawer"]
        UI --> Slider
        UI --> GenDash
        UI --> SecModal
        UI --> CitationDrawer
    end

    subgraph API_Gateway ["Application Server & API Boundary (Port 8005)"]
        FastAPI["FastAPI REST Router (/api/*)"]
        CORS["CORS & Origin Whitelist"]
        Pydantic["Pydantic v2 Request Validators"]
        FastAPI --> CORS
        FastAPI --> Pydantic
    end

    subgraph Security_Shield ["Defense-in-Depth Security Guardrails"]
        UnicodeNorm["Unicode NFKD Normalizer"]
        ZeroWidth["Zero-Width Evasion Stripper"]
        SQLiShield["SQLi AST Tokenizer & Shield"]
        LeakScrubber["Credential & Schema Redactor"]
        AuditLogger["Immutable Security Audit Logger"]
    end

    subgraph Core_Engines ["Autonomous Agentic Core"]
        Orchestrator["AgentOrchestrator"]
        Router["Deterministic Tool Router"]
        TruthEng["TruthEngine (Thermal Physics)"]
        ConflictEng["ConflictEngine (Tri-Directional Cross-Check)"]
        MemoryEng["Dual-Tier MemoryEngine (L1 Fleet / L2 User)"]
        ComplianceEng["ComplianceEngine (OPS-1 to OPS-6, SR-01)"]
        LLMGateway["Model-Agnostic LLM Client (Gemini / OpenRouter)"]
    end

    subgraph Storage_Tier ["Analytical Storage Tier (SQLite 3 WAL)"]
        RelationalDB[("Relational Tables<br/>wells, inspections, maintenance,<br/>context_notes, security_logs")]
        FTS5Index[("FTS5 Virtual Tables<br/>fleet_docs_fts, maintenance_reports_fts")]
        BTreeIndex["Compound B-Tree Indices<br/>(asset_id, date), (area_id)"]
    end

    UI -->|"HTTP/JSON via Vite Proxy"| FastAPI
    FastAPI --> UnicodeNorm
    UnicodeNorm --> ZeroWidth
    ZeroWidth --> SQLiShield
    SQLiShield --> Orchestrator
    
    Orchestrator --> Router
    Router --> TruthEng
    Router --> ConflictEng
    Router --> MemoryEng
    Router --> ComplianceEng
    Router --> LLMGateway
    
    TruthEng --> RelationalDB
    ConflictEng --> RelationalDB
    ComplianceEng --> RelationalDB
    Router --> FTS5Index
    RelationalDB --- BTreeIndex
    
    Orchestrator --> LeakScrubber
    LeakScrubber --> FastAPI
    SQLiShield -.->|"Threat Log"| AuditLogger
    AuditLogger --> RelationalDB
```

---

## 2. Class Diagram (UML Class)

Illustrates the object-oriented structure, class relationships, and method signatures across the backend architecture.

```mermaid
classDiagram
    class AgentOrchestrator {
        -str db_path
        -LLMClient llm_client
        +process_query(user_id: str, session_id: str, query: str) CopilotResponse
        -_save_turn(session_id: str, user_id: str, query: str, resp: CopilotResponse) void
    }

    class CopilotResponse {
        +str answer_markdown
        +str visual_type
        +Any visual_data
        +List~str~ citations
        +Optional~str~ conflict_warning
        +List~str~ entities_discussed
        +List~str~ tools_called
    }

    class TruthEngine {
        +get_well_latest_status(asset_id: str) Dict
        +get_non_producing_wells_in_area(area: str) List
        +calculate_thermal_differential(t_wellhead: float, t_ambient: float) float
        +evaluate_production_threshold(well_type: str, delta_c: float) bool
    }

    class ConflictEngine {
        +audit_spill_detection_validity(asset_id: str, inspection_id: str) Dict
        +verify_user_claim(user_id: str, asset_id: str, claim: str) Dict
        +reconcile_inspector_notes(notes: List) Dict
    }

    class MemoryEngine {
        +save_private_chat_message(session_id: str, user_id: str, role: str, content: str) void
        +get_user_private_memory(user_id: str, lookback_days: int) Dict
        +record_fleet_truth_override(user_id: str, asset_id: str, field: str, value: Any) Dict
        +get_fleet_shared_overrides(asset_id: str) List
    }

    class ComplianceEngine {
        +audit_ops1_gas_odor_responses(since_date: str) Dict
        +audit_ops2_flowline_bypasses() Dict
        +audit_ops3_status_precedence() Dict
        +audit_ops5_freeze_protection() Dict
        +audit_regulator_spill_letters() Dict
    }

    class LLMClient {
        -str gemini_key
        -str openrouter_key
        -str model_name
        +generate_chat_response(system_prompt: str, messages: List) str
        +generate_structured_sql(query: str, schema_ddl: str) str
    }

    class SecurityGuardrails {
        +normalize_text_for_security_scan(text: str) str
        +check_prompt_injection(query: str) Tuple~bool, str~
        +check_sql_injection_attempt(query: str) Tuple~bool, str~
        +sanitize_response_for_leaks(response_text: str) str
        +log_security_event(event_type: str, severity: str, user_id: str, details: Dict) void
    }

    AgentOrchestrator --> LLMClient : delegates synthesis to
    AgentOrchestrator --> CopilotResponse : constructs
    AgentOrchestrator ..> TruthEngine : queries physical truth
    AgentOrchestrator ..> ConflictEngine : checks contradictions
    AgentOrchestrator ..> MemoryEngine : isolates/updates state
    AgentOrchestrator ..> ComplianceEngine : audits SOP rules
    AgentOrchestrator ..> SecurityGuardrails : enforces policies
```

---

## 3. Sequence Diagram: End-to-End Query Lifecycle (UML Sequence)

Traces the execution sequence of an operational audit query (e.g. Q3 Gas Odor Response Audit or Q6 Status Disagreement) through the security, reasoning, and storage subsystems.

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Field Operator / Supervisor
    participant UI as React Generative UI
    participant Gateway as FastAPI Endpoint (/api/chat)
    participant Guard as Security Guardrails
    participant Orch as AgentOrchestrator
    participant Truth as Truth & Compliance Engine
    participant DB as SQLite Analytical DB & FTS5
    participant LLM as Google Gemini / LLM Gateway

    Operator->>UI: Enters query ("Gas odor response audit since 1 Nov 2026")
    UI->>Gateway: POST /api/chat {user_id, session_id, message}
    
    Gateway->>Guard: normalize_text_for_security_scan(message)
    Guard->>Guard: Strip zero-width chars & unicode homoglyphs
    Guard->>Guard: Evaluate injection AST & SQLi tokens
    
    alt Threat Detected
        Guard-->>Gateway: Refusal payload
        Gateway-->>UI: Blocked response (403/Policy notice)
    else Input Clean
        Guard->>Orch: process_query(user_id, session_id, clean_query)
        
        Orch->>Orch: Extract entity references (WELL-xxxx, Sectors)
        Orch->>Truth: audit_ops1_gas_odor_responses("2026-11-01")
        
        Truth->>DB: Query context_notes (gas odor reports)
        DB-->>Truth: 26 gas odor incident rows
        
        Truth->>DB: Cross-reference maintenance & manual inspections
        DB-->>Truth: Matching response timestamps
        
        Truth->>Truth: Apply OPS-1 deadlines (24h before 2027, 12h from 2027)
        Truth-->>Orch: Structured audit records & Met/Missed tallies
        
        opt Narrative Polish / Synthesis
            Orch->>LLM: Format explanation with context & citations
            LLM-->>Orch: Formatted markdown summary
        end
        
        Orch->>Guard: sanitize_response_for_leaks(markdown)
        Guard-->>Orch: Cleaned markdown (credentials & schema scrubbed)
        
        Orch->>DB: Persist turn in private_chat_messages
        Orch-->>Gateway: CopilotResponse {markdown, visual_type='table', citations}
        Gateway-->>UI: JSON HTTP 200 Response
        UI->>Operator: Renders interactive table, citations, and contextual slider
    end
```

---

## 4. State Machine Diagram: Well Status Derivation & OPS-3 Precedence (UML State)

Depicts how raw sensor telemetry, temperature delta physics, and operator handover notes transition a well's authoritative operational status.

```mermaid
stateDiagram-v2
    [*] --> IngestTelemetry : Aerial Drone / SCADA Sensor Reading
    
    state IngestTelemetry {
        ComputeDelta: Delta_T = T_wellhead - T_ambient
    }
    
    ComputeDelta --> EvaluatePhysics : Check Well Model Threshold
    
    state EvaluatePhysics {
        T200_Check: Delta_T >= 15.0 °C ?
        T350_Check: Delta_T >= 10.0 °C ?
    }
    
    EvaluatePhysics --> PhysicalCold : Delta_T < Threshold
    EvaluatePhysics --> PhysicalHot : Delta_T >= Threshold
    
    state OPS3_Precedence_Resolution {
        CheckNotes: Inspect latest context_notes after inspection date
    }
    
    PhysicalCold --> OPS3_Precedence_Resolution
    PhysicalHot --> OPS3_Precedence_Resolution
    
    OPS3_Precedence_Resolution --> Status_Producing : PhysicalHot AND (No Note OR Restart Note)
    OPS3_Precedence_Resolution --> Status_ShutIn : PhysicalHot AND Shut-in Note Post-Dates Inspection (OPS-3 §1)
    OPS3_Precedence_Resolution --> Status_Unconfirmed : PhysicalCold AND Restart Note Post-Dates Inspection (OPS-3 §2)
    OPS3_Precedence_Resolution --> Status_Offline : PhysicalCold AND (No Note OR Shut-in Note)
    
    state Status_Producing {
        [*] --> ProducingState
        ProducingState: Verified Active Production
    }
    
    state Status_ShutIn {
        [*] --> ShutInState
        ShutInState: Not Producing (Shut-in per Operator Note)
    }
    
    state Status_Unconfirmed {
        [*] --> UnconfirmedState
        UnconfirmedState: Producing (Unconfirmed until Telemetry Verifies)
    }
    
    state Status_Offline {
        [*] --> OfflineState
        OfflineState: Confirmed Non-Producing
    }
    
    Status_Producing --> [*]
    Status_ShutIn --> [*]
    Status_Unconfirmed --> [*]
    Status_Offline --> [*]
```

---

## 5. Use Case Diagram (UML Use Case)

Illustrates user interactions by organizational role across the operational, environmental, and engineering domains.

```mermaid
graph LR
    subgraph Personas ["Fleet Operations Roles"]
        Operator["Field Operator<br/>(Shift Pumper)"]
        Supervisor["Production Supervisor<br/>(Michael Turner / Nathan Pierce)"]
        HSE["HSE Auditor<br/>(Laura Simmons / Chris Dalton)"]
    end

    subgraph Copilot_Capabilities ["Copilot System Capabilities"]
        UC1["Check Real-Time Well Production Status"]
        UC2["Reconcile Disagreeing Statuses (OPS-3)"]
        UC3["Audit Gas Odor Response Deadlines (OPS-1)"]
        UC4["Verify Temporary Flowline Bypasses (OPS-2)"]
        UC5["Audit Regulatory Spills & Soil Lab Reports (SR-01)"]
        UC6["Rank Operator Acoustic & Vibration Anomalies"]
        UC7["Track Supplier Recalled Pumps (HPC-RN-2026-07)"]
        UC8["Analyze Shut-in Delays (Weather/Parts/Crews)"]
        UC9["Log Verified Data Corrections & Verbal Overrides"]
        UC10["Recall Private Multi-Turn Conversational Memory"]
        UC11["Pivot Visuals (Text / Table / Line / Heatmap / Map)"]
    end

    Operator --> UC1
    Operator --> UC6
    Operator --> UC9
    Operator --> UC11

    Supervisor --> UC1
    Supervisor --> UC2
    Supervisor --> UC7
    Supervisor --> UC8
    Supervisor --> UC9
    Supervisor --> UC10
    Supervisor --> UC11

    HSE --> UC3
    HSE --> UC4
    HSE --> UC5
    HSE --> UC11
```

---

## 6. Entity-Relationship (ER) Schema Diagram

Details the relational tables, primary/foreign keys, and virtual FTS5 indices supporting sub-second analytical retrieval.

```mermaid
erDiagram
    AREAS ||--o{ WELLS : contains
    WELLS ||--o{ INSPECTIONS : receives
    WELLS ||--o{ MAINTENANCE : undergoes
    WELLS ||--o{ CONTEXT_NOTES : logs
    USERS ||--o{ INSPECTIONS : conducts
    USERS ||--o{ PRIVATE_CHAT_MESSAGES : owns
    
    AREAS {
        string area_id PK
        string name
        string bounds_geojson
    }

    WELLS {
        string asset_id PK
        string area_id FK
        string name
        string well_type
        float latitude
        float longitude
        string recorded_status
        string decommissioned_on
    }

    INSPECTIONS {
        string inspection_id PK
        string asset_id FK
        string inspected_date
        float wellhead_temp_c
        float ambient_temp_c
        int spill_detected
        float spill_est_volume_bbl
        string method
        string inspector_user_id FK
    }

    MAINTENANCE {
        string maintenance_id PK
        string asset_id FK
        string started_at
        string completed_at
        string issue
        string action_taken
        float cost_usd
        string report_file
    }

    CONTEXT_NOTES {
        string note_id PK
        string asset_id FK
        string author_user_id FK
        string created_at
        string note_type
        string text
    }

    PRIVATE_CHAT_MESSAGES {
        int id PK
        string session_id
        string user_id FK
        string role
        string content
        string visual_json
        string created_at
    }

    FLEET_DOCS_FTS {
        string doc_id PK
        string title
        string content
    }

    MAINTENANCE_REPORTS_FTS {
        string maintenance_id PK
        string report_file
        string report_text
    }
```
